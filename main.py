import os
import sys

import csv
import sqlite3
from PyQt5.QtCore import Qt
from PyQt5 import uic, QtGui
import datetime

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QDialog, QTableWidgetItem, QMessageBox, QLineEdit, \
    QAbstractItemView, QMenuBar, QAction, QFileDialog

current_user = ''


def SaveToHistory(items, user, action, table):
    time = datetime.datetime.today().replace(microsecond=0)
    time = time.strftime('%d.%m.%Y %H:%M:%S')
    con = sqlite3.connect("database\\shop_database.db")
    cur = con.cursor()
    userId = (cur.execute(f'SELECT userId FROM users WHERE login LIKE "{user}"').fetchall()[0])[0]
    actionId = (cur.execute(f'SELECT actionId FROM actions WHERE actionName LIKE "{action}"').fetchall()[0])[0]
    if action == 'CREATE':
        itemId = items[0]
        cur.execute(
            f"INSERT INTO history(userId, actionId, itemId, tableName, time) VALUES({userId}, {actionId}, {itemId}, "
            f"'{table}', '{time}')").fetchall()
        con.commit()
    elif action == 'DELETE' and len(items) == 1:
        itemId = items[0]
        cur.execute(
            f"INSERT INTO history(userId, actionId, itemId, tableName, time) VALUES({userId}, {actionId}, {itemId}, "
            f"'{table}', '{time}')").fetchall()
        con.commit()
    elif len(items) > 1:
        for itemId in items:
            cur.execute(
                f"INSERT INTO history(userId, actionId, itemId, tableName, time) VALUES({userId}, {actionId}, "
                f"{itemId}, '{table}', '{time}')").fetchall()
            con.commit()
    else:
        itemId = items
        cur.execute(
            f"INSERT INTO history(userId, actionId, itemId, tableName, time) VALUES({userId}, {actionId}, {itemId}, "
            f"'{table}', '{time}')").fetchall()
        con.commit()


def FillTable(table, table_name):
    con = sqlite3.connect("database\\shop_database.db")
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = 0")
    con.commit()
    result = cur.execute(f"SELECT * FROM {table_name}").fetchall()
    table.setRowCount(len(result))
    table.setColumnCount(len(result[0]))
    titles = [description[0] for description in cur.description]
    table.setHorizontalHeaderLabels(titles)
    for i, elem in enumerate(result):
        for j, val in enumerate(elem):
            table.setItem(i, j, QTableWidgetItem(str(val)))
    con.close()


class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi('design\\login_window.ui', self)
        self.setFixedSize(700, 300)
        self.autorize_btn.clicked.connect(self.login)
        self.autorize = False
        self.accounts = []
        self.password_line.setEchoMode(QLineEdit.Password)
        self.current_user = current_user
        self.show_pass.stateChanged.connect(self.show_password)
        con = sqlite3.connect("database\\shop_database.db")
        cur = con.cursor()
        result = cur.execute("""SELECT * FROM users""").fetchall()
        for elem in result:
            self.accounts.append((elem[4], elem[5]))
        con.close()

    def login(self):
        global current_user
        for account in self.accounts:
            if self.login_line.text() == account[0] and self.password_line.text() == account[1]:
                self.autorize = True
                break
        if self.autorize:
            current_user = self.login_line.text()
            self.hide()
            self.accept()
        else:
            palette = self.error_label.palette()
            palette.setColor(QtGui.QPalette.WindowText, QtGui.QColor("red"))
            self.error_label.setPalette(palette)
            self.error_label.setText('Неверный логин или пароль')

    def show_password(self, check):
        if check == Qt.Checked:
            self.password_line.setEchoMode(QLineEdit.Normal)
        else:
            self.password_line.setEchoMode(QLineEdit.Password)


class ProfileWindow(QWidget):
    def __init__(self, lastName, name, age, position):
        super().__init__()
        uic.loadUi('design\\profile_menu.ui', self)
        self.setFixedSize(610, 385)
        self.close_button.clicked.connect(self.close_menu)
        self.lastName_label.setText(lastName)
        self.name_label.setText(name)
        self.age_label.setText(age)
        if position == 1:
            position = "Администратор"
        else:
            position = 'Пользователь'
        self.level_label.setText(position)

    def close_menu(self):
        self.close()


class SortingWindow(QWidget):
    def __init__(self, table, table_name):
        super().__init__()
        uic.loadUi('design\\sorting_menu.ui', self)
        self.table = table
        self.con = sqlite3.connect("database\\shop_database.db")
        self.table_name = table_name
        self.sort_button.clicked.connect(self.sorting)
        self.default_button.clicked.connect(self.SetDefault)

    def sorting(self):
        try:
            self.error_label.setText('')
            command = self.SQL_command.toPlainText()
            if self.table_name in command:
                cur = self.con.cursor()
                result = cur.execute(command).fetchall()
                self.table.setRowCount(len(result))
                self.table.setColumnCount(len(result[0]))
                self.titles = [description[0] for description in cur.description]
                self.table.setHorizontalHeaderLabels(self.titles)
                for i, elem in enumerate(result):
                    for j, val in enumerate(elem):
                        self.table.setItem(i, j, QTableWidgetItem(str(val)))
            else:
                self.error_label.setText('Вы пытаетесь искать в другой таблице.')
        except Exception:
            self.error_label.setText('Ошибка!')

    def SetDefault(self):
        cur = self.con.cursor()
        result = cur.execute(f'SELECT * FROM {self.table_name}').fetchall()
        self.table.setRowCount(len(result))
        self.table.setColumnCount(len(result[0]))
        self.titles = [description[0] for description in cur.description]
        self.table.setHorizontalHeaderLabels(self.titles)
        for i, elem in enumerate(result):
            for j, val in enumerate(elem):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))


class HistoryWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('design\\history_menu.ui', self)
        self.table_name = 'history'
        self.sort_button.clicked.connect(self.open_sorting)
        self.sorting = SortingWindow(self.history_table, self.table_name)
        self.update_button.clicked.connect(self.update_table)
        self.setFixedSize(670, 660)
        try:
            FillTable(self.history_table, self.table_name)
            self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.history_table.horizontalHeader().setStretchLastSection(True)
        except Exception:
            pass

    def open_sorting(self):
        self.sorting.show()

    def update_table(self):
        try:
            FillTable(self.history_table, self.table_name)
            self.history_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        except Exception:
            pass


class AddProductWindow(QWidget):
    def __init__(self, table, table_name):
        super().__init__()
        self.action = 'CREATE'
        self.table = table
        self.table_name = table_name
        uic.loadUi('design\\add_products.ui', self)
        self.add_button.clicked.connect(self.add_product)

    def add_product(self):
        name = self.name_line.text()
        count = self.count.value()
        price = self.price_line.text()
        try:
            con = sqlite3.connect("database\\shop_database.db")
            cur = con.cursor()
            cur.execute(f"INSERT INTO products(name, price, count) VALUES('{name}', {int(price)}, {count}) ").fetchall()
            con.commit()
            QMessageBox.about(self, 'Успешно', 'Вы успешно добавили товар')
            FillTable(self.table, self.table_name)
            con = sqlite3.connect("database\\shop_database.db")
            cur = con.cursor()
            result = (cur.execute('SELECT MAX(itemId) from products').fetchall())[0]
            SaveToHistory(result, current_user, self.action, self.table_name)
        except Exception:
            QMessageBox.warning(self, 'Ошибка!', "Вы ввели неккоректные данные")


class EditProductWindow(QDialog):
    def __init__(self, table, table_name, id, action):
        super().__init__()
        uic.loadUi('design\\edit_products.ui', self)
        self.action = action
        self.id = id
        self.table = table
        self.table_name = table_name
        self.ProductId = self.table.item(self.id[0], 0).text()
        con = sqlite3.connect("database\\shop_database.db")
        cur = con.cursor()
        name, price, count = \
            (cur.execute(f"SELECT name, price, count FROM products WHERE ItemId = {self.ProductId}").fetchall())[0]
        price = str(price)
        self.name_line.setText(name)
        self.count.setValue(count)
        self.price_line.setText(price)
        self.edit_button.clicked.connect(self.edit_product)

    def edit_product(self):
        name = self.name_line.text()
        count = self.count.value()
        price = self.price_line.text()
        try:
            con = sqlite3.connect("database\\shop_database.db")
            cur = con.cursor()
            cur.execute(f'UPDATE products \n'
                        f"SET (name, price, count) = ('{name}', {int(price)}, {count}) \n"
                        f'WHERE itemid = {int(self.ProductId)}')
            con.commit()
            QMessageBox.about(self, 'Успешно', 'Вы успешно изменили товар')
            FillTable(self.table, self.table_name)
            SaveToHistory(self.ProductId, current_user, self.action, self.table_name)
            self.hide()
        except Exception:
            QMessageBox.warning(self, 'Ошибка!', "Вы ввели неккоректные данные")


class ProductsWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.menu_bar()
        uic.loadUi('design\\products_menu.ui', self)
        self.table_name = 'products'
        self.action = ''
        self.sort_button.clicked.connect(self.open_sorting)
        self.editProduct.clicked.connect(self.edit_product)
        self.addProduct.clicked.connect(self.add_product)
        self.sorting = SortingWindow(self.products_table, self.table_name)
        self.add_product_menu = AddProductWindow(self.products_table, self.table_name)
        self.deleteProduct.clicked.connect(self.delete_product)
        try:
            FillTable(self.products_table, self.table_name)
        except Exception:
            pass
        self.products_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def open_sorting(self):
        self.sorting.show()

    def delete_product(self):
        con = sqlite3.connect("database\\shop_database.db")
        cur = con.cursor()
        result = cur.execute(f"SELECT * FROM products").fetchall()
        cur.execute("PRAGMA foreign_keys = 0")
        con.commit()
        self.action = 'DELETE'
        rows = list(set([i.row() for i in self.products_table.selectedItems()]))
        if len(rows) == len(result):
            QMessageBox.warning(self, 'Ошибка!', 'Нельзя удалять все элементы.')
        elif len(rows) > 0:
            ids = [self.products_table.item(i, 0).text() for i in rows]
            if len(rows) == 1:
                valid = QMessageBox.question(
                    self, '', f"Действительно удалить элемент с id {', '.join(ids)}?",
                    QMessageBox.Yes, QMessageBox.No)
            else:
                valid = QMessageBox.question(
                    self, '', f"Действительно удалить элементы с id {', '.join(ids)}?",
                    QMessageBox.Yes, QMessageBox.No)
            if valid == QMessageBox.Yes:
                con = sqlite3.connect("database\\shop_database.db")
                cur = con.cursor()
                cur.execute("DELETE FROM products WHERE itemId IN (" + ", ".join('?' * len(ids)) + ")", ids)
                con.commit()
                FillTable(self.products_table, self.table_name)
                SaveToHistory(ids, current_user, self.action, self.table_name)
        else:
            QMessageBox.warning(self, 'Ошибка!', 'Вы не выбрали ни одного элемента')

    def add_product(self):
        self.add_product_menu.show()

    def edit_product(self):
        self.action = 'EDIT'
        row = list(set([i.row() for i in self.products_table.selectedItems()]))
        if len(row) == 0:
            QMessageBox.warning(self, 'Ошибка!', "Вы не выбрали строку")
        elif len(row) > 1:
            QMessageBox.warning(self, 'Ошибка!', "Вы выбрали больше 1 строки")
        else:
            self.edit_product_menu = EditProductWindow(self.products_table, self.table_name, row, self.action)
            self.edit_product_menu.show()

    def menu_bar(self):
        self.menuBar = QMenuBar(self)
        menu = self.menuBar.addMenu("Меню")
        loadAction = QAction('Открыть', self)
        menu.addAction(loadAction)
        loadAction.triggered.connect(self.load_as_csv)
        saveAction = QAction('Сохранить как', self)
        menu.addAction(saveAction)
        saveAction.triggered.connect(self.save_as_csv)
        self.menuBar.show()

    def load_as_csv(self):
        csvTable = QFileDialog.getOpenFileName(self, 'Выбрать таблицу', '', 'Таблица (*.csv)')[0]
        try:
            with open(csvTable, encoding='utf-8') as csvFile:
                reader = csv.reader(csvFile, delimiter=';', quotechar='"')
                con = sqlite3.connect("database\\shop_database.db")
                cur = con.cursor()
                cur.execute(f"DROP table products")
                con.commit()
                cur.execute(f"CREATE TABLE products (itemId INTEGER PRIMARY KEY AUTOINCREMENT UNIQUE NOT NULL,"
                            f" name   TEXT    UNIQUE NOT NULL, price  INT NOT NULL, count  INT NOT NULL);")
                con.commit()
                for row in reader:
                    name, price, count = row[0], row[1], row[2]
                    cur.execute(f"INSERT INTO products(name, price, count) "
                                f"VALUES('{name}', {int(price)}, {count}) ").fetchall()
                    con.commit()
                FillTable(self.products_table, self.table_name)
                QMessageBox.about(self, 'Успешно!', 'Таблица была успешно импортирована.')

        except Exception:
            QMessageBox.warning(self, 'Ошибка!', 'Таблица содержит неверные данные.')

    def save_as_csv(self):
        con = sqlite3.connect("database\\shop_database.db")
        cur = con.cursor()
        result = cur.execute(f"SELECT * FROM products").fetchall()
        with open('data\\save_data.csv', 'w', newline='', encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile, delimiter=';', quotechar='"')
            for row in result:
                writer.writerow(row[1:])
        result = []
        with open('data\\save_data.csv', 'r', newline='', encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile, delimiter=';', quotechar='"')
            for row in reader:
                result.append(row)
        try:
            save_file = QFileDialog.getSaveFileName(self, 'Сохранить таблицу', '', 'Таблица (*.csv)')[0]
            with open(save_file, 'w', newline='', encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile, delimiter=';', quotechar='"')
                for row in result:
                    writer.writerow(row)
            QMessageBox.about(self, 'Успешно!', "Файл успешно сохранён")
        except Exception:
            QMessageBox.warning(self, 'Ошибка!', "Произошла ошибка при сохранении файла.")
        os.remove('data\\save_data.csv')


class AddUserWindow(QWidget):
    def __init__(self, table, table_name):
        super().__init__()
        uic.loadUi('design\\add_user.ui', self)
        self.action = "CREATE"
        self.table = table
        self.table_name = table_name
        self.addUser.clicked.connect(self.add_user)

    def add_user(self):
        try:
            name = self.name_line.text()
            lastName = self.lastName_line.text()
            login = self.login_line.text()
            password = self.password_line.text()
            age = self.age_choose.value()
            position = (self.position_choose.currentText().split('-'))[0]
            for i in (name, lastName, login, password, age, position):
                if i == '':
                    raise ZeroDivisionError
            con = sqlite3.connect("database\\shop_database.db")
            cur = con.cursor()
            cur.execute(
                f"INSERT INTO users(lastName, name, age, login, password, position) VALUES('{lastName}', '{name}', "
                f"{age}, '{login}', '{password}', {position}) ").fetchall()
            con.commit()
            QMessageBox.about(self, 'Успешно', 'Вы успешно добавили пользователя')
            FillTable(self.table, self.table_name)
            con = sqlite3.connect("database\\shop_database.db")
            cur = con.cursor()
            result = (cur.execute('SELECT MAX(userId) from users').fetchall())[0]
            SaveToHistory(result, current_user, self.action, self.table_name)
        except ZeroDivisionError:
            QMessageBox.warning(self, 'Ошибка!', "Вы ввели неккоректные данные")


class EditUserWindow(QDialog):
    def __init__(self, table, table_name, id, action):
        super().__init__()
        uic.loadUi('design\\edit_user.ui', self)
        self.action = action
        self.table = table
        self.table_name = table_name
        self.id = id
        self.userId = self.table.item(self.id[0], 0).text()
        con = sqlite3.connect("database\\shop_database.db")
        cur = con.cursor()
        lastName, name, age, login, password, position = (cur.execute(
            f"SELECT lastName, name, age, login, password, position FROM users WHERE userId = {self.userId}").fetchall())[
            0]
        self.name_line.setText(name)
        self.lastName_line.setText(lastName)
        self.login_line.setText(login)
        self.password_line.setText(password)
        self.age_choose.setValue(int(age))
        self.editUser.clicked.connect(self.edit_user)

    def edit_user(self):
        lastName = self.lastName_line.text()
        name = self.name_line.text()
        age = self.age_choose.value()
        login = self.login_line.text()
        password = self.password_line.text()
        position = (self.position_choose.currentText().split('-'))[0]
        try:
            for i in (name, lastName, login, password, age, position):
                if i == '':
                    raise ZeroDivisionError
            con = sqlite3.connect("database\\shop_database.db")
            cur = con.cursor()
            cur.execute(f'UPDATE users \n'
                        f"SET (lastName, name, age, login, password, position) = ('{lastName}', '{name}', {age}, '{login}', '{password}', {position}) \n"
                        f'WHERE userId = {self.userId}')
            con.commit()
            QMessageBox.about(self, 'Успешно', 'Вы успешно изменили товар')
            FillTable(self.table, self.table_name)
            SaveToHistory(self.userId, current_user, self.action, self.table_name)
            self.hide()
        except ZeroDivisionError:
            QMessageBox.warning(self, 'Ошибка!', "Вы ввели неккоректные данные")


class UsersWindow(QWidget):
    def __init__(self):
        super().__init__()
        uic.loadUi('design\\users_menu.ui', self)
        self.table_name = 'users'
        self.action = ''
        self.sort_button.clicked.connect(self.open_sorting)
        self.addUser.clicked.connect(self.add_user)
        self.editUser.clicked.connect(self.edit_user)
        self.deleteUser.clicked.connect(self.delete_user)
        self.addUsers = AddUserWindow(self.users_table, self.table_name)
        self.sorting = SortingWindow(self.users_table, self.table_name)
        FillTable(self.users_table, self.table_name)
        self.users_table.setEditTriggers(QAbstractItemView.NoEditTriggers)

    def open_sorting(self):
        self.sorting.show()

    def delete_user(self):
        con = sqlite3.connect("database\\shop_database.db")
        cur = con.cursor()
        result = cur.execute(f"SELECT * FROM users").fetchall()
        cur.execute("PRAGMA foreign_keys = 0")
        con.commit()
        self.action = 'DELETE'
        rows = list(set([i.row() for i in self.users_table.selectedItems()]))
        if len(rows) == len(result):
            QMessageBox.warning(self, 'Ошибка!', 'Нельзя удалять все элементы.')
        elif len(rows) > 0:
            ids = [self.users_table.item(i, 0).text() for i in rows]
            if len(rows) == 1:
                valid = QMessageBox.question(
                    self, '', f"Действительно удалить элемент с id {', '.join(ids)}?",
                    QMessageBox.Yes, QMessageBox.No)
            else:
                valid = QMessageBox.question(
                    self, '', f"Действительно удалить элементы с id {', '.join(ids)}?",
                    QMessageBox.Yes, QMessageBox.No)
            if valid == QMessageBox.Yes:
                SaveToHistory(ids, current_user, self.action, self.table_name)
                con = sqlite3.connect("database\\shop_database.db")
                cur = con.cursor()
                cur.execute("DELETE FROM users WHERE userId IN (" + ", ".join('?' * len(ids)) + ")", ids)
                con.commit()
                FillTable(self.users_table, self.table_name)
        else:
            QMessageBox.warning(self, 'Ошибка!', 'Вы не выбрали ни одного элемента')

    def add_user(self):
        self.addUsers.show()

    def edit_user(self):
        self.action = "EDIT"
        row = list(set([i.row() for i in self.users_table.selectedItems()]))
        if len(row) == 0:
            QMessageBox.warning(self, 'Ошибка!', "Вы не выбрали строку")
        elif len(row) > 1:
            QMessageBox.warning(self, 'Ошибка!', "Вы выбрали больше 1 строки")
        else:
            self.edit_users_menu = EditUserWindow(self.users_table, self.table_name, row, self.action)
            self.edit_users_menu.show()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('design\\main_window.ui', self)
        self.setFixedSize(740, 290)
        self.profile_button.clicked.connect(self.open_profile)
        self.history_button.clicked.connect(self.open_history)
        self.products_button.clicked.connect(self.open_products)
        self.users_button.clicked.connect(self.open_users)
        self.change_profile_trigger.triggered.connect(self.change_user)
        self.exit_trigger.triggered.connect(self.exit_system)
        self.current_user = current_user
        con = sqlite3.connect("database\\shop_database.db")
        cur = con.cursor()
        self.user_info = (cur.execute(f"""SELECT * FROM users WHERE login LIKE '{self.current_user}'""").fetchall())[0]
        con.close()
        lastName, name, age, position = self.user_info[1], self.user_info[2], str(self.user_info[3]), self.user_info[-1]
        self.position = position
        self.profile_menu = ProfileWindow(lastName, name, age, position)
        self.history_menu = HistoryWindow()
        self.products_menu = ProductsWindow()
        self.users_menu = UsersWindow()

    def open_profile(self):
        self.profile_menu.show()

    def open_history(self):
        self.error_label.setText('')
        if self.position == 1:
            self.history_menu.show()
        else:
            QMessageBox.warning(self, 'Ошибка!', 'У вас нет доступа к данной категории')

    def open_products(self):
        self.products_menu.show()

    def open_users(self):
        self.error_label.setText('')
        if self.position == 1:
            self.users_menu.show()
        else:
            QMessageBox.warning(self, 'Ошибка!', 'У вас нет доступа к данной категории')

    def change_user(self):
        self.profile_menu.close()
        self.history_menu.close()
        self.history_menu.sorting.close()
        self.products_menu.close()
        self.products_menu.sorting.close()
        self.products_menu.add_product_menu.close()
        self.users_menu.sorting.close()
        self.users_menu.addUsers.close()
        self.users_menu.close()
        self.hide()
        login = LoginWindow()
        if login.exec_() == QDialog.Accepted:
            con = sqlite3.connect("database\\shop_database.db")
            cur = con.cursor()
            self.user_info = \
                (cur.execute(f"""SELECT * FROM users WHERE login LIKE '{current_user}'""").fetchall())[0]
            con.close()
            lastName, name, age, position = self.user_info[1], self.user_info[2], str(self.user_info[3]), \
                                            self.user_info[-1]
            self.profile_menu = ProfileWindow(lastName, name, age, position)
            self.position = position
            self.show()

    def exit_system(self):
        valid = QMessageBox.question(
            self, 'Подтверждение выхода', f"Вы действительно хотите покинуть систему?",
            QMessageBox.Yes, QMessageBox.No)
        if valid == QMessageBox.Yes:
            self.profile_menu.close()
            self.history_menu.close()
            self.history_menu.sorting.close()
            self.products_menu.close()
            self.products_menu.sorting.close()
            self.products_menu.add_product_menu.close()
            self.products_menu.edit_product_menu.close()
            self.users_menu.sorting.close()
            self.users_menu.addUsers.close()
            self.users_menu.edit_users_menu.close()
            self.users_menu.close()
            self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    login = LoginWindow()
    if login.exec_() == QDialog.Accepted:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
