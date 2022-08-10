from random import randint
import sqlite3


class BankAccount:
    def __init__(self, uid=None, card=None, pin=None, balance=0):
        self.id = uid
        self.card = card or self.generate_card_number()
        self.pin = pin or self.generate_pin()
        self.balance = balance

    def generate_card_number(self):
        iin = '400000'
        can = ''.join(str(randint(0, 9)) for _ in range(9))
        checksum = self.luhn(iin + can)
        return iin + can + checksum

    @staticmethod
    def luhn(card):
        nums = [int(i) for i in card[1::2]]
        for i in card[::2]:
            n = int(i) * 2
            if n > 9:
                n -= 9
            nums.append(n)
        return str((10 - sum(nums) % 10) % 10)

    @staticmethod
    def generate_pin():
        return ''.join(str(randint(0, 9)) for _ in range(4))


class ABS:
    main_menu = ('1. Create an account', '2. Log into account', '0. Exit')
    user_menu = ('1. Balance', '2. Add income', '3. Do transfer', '4. Close account', '5. Log out', '0. Exit')

    def __init__(self, database):
        self.connection = sqlite3.connect(database)
        self.cursor = self.connection.cursor()
        self.cursor.execute('DROP TABLE IF EXISTS card;')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS card
            (id INTEGER PRIMARY KEY,
            number TEXT NOT NULL UNIQUE,
            pin TEXT NOT NULL,
            balance INTEGER DEFAULT 0);
            ''')
        self.connection.commit()

    def main(self):
        while True:
            print(*ABS.main_menu, sep='\n')

            user_input = int(input())
            if user_input == 1:
                self.create_account()
            elif user_input == 2:
                logged_user = self.login()
                if logged_user:
                    print('\nYou have successfully logged in!\n')
                    self.account_actions(logged_user)
                else:
                    print('\nWrong card number or PIN!\n')
            elif user_input == 0:
                self.connection.close()
                print('\nBye!')
                exit()
            else:
                print('Wrong input\n')
                continue

    def create_account(self):
        new = BankAccount()
        self.cursor.execute('INSERT INTO card (number, pin, balance) VALUES (?, ?, 0);', (new.card, new.pin))
        self.connection.commit()
        print('\nYour card has been created',
              'Your card number:', new.card,
              'Your card PIN:', new.pin,
              sep='\n')
        print()

    def login(self):
        login_card = input('Enter your card number:\n')
        login_pin = input('Enter your PIN:\n')
        self.cursor.execute(f'SELECT * FROM card WHERE number = "{login_card}" AND pin = "{login_pin}";')
        return self.cursor.fetchone()

    def account_actions(self, logged):
        user = BankAccount(*logged)  # user.id, user.card, user.pin, user.balance

        while True:
            print(*ABS.user_menu, sep='\n')

            user_input = int(input())
            if user_input == 1:
                print(f'\nBalance: {user.balance}\n')
            elif user_input == 2:
                print('Enter income:')
                user.balance += int(input())
                self.cursor.execute('UPDATE card SET balance = ? WHERE id = ?;', (user.balance, user.id))
                self.connection.commit()
                print('Income was added!\n')
            elif user_input == 3:
                print(self.do_transfer(user) + '\n')
            elif user_input == 4:
                self.cursor.execute(f'DELETE FROM card WHERE id = {user.id};')
                self.connection.commit()
                print('\nThe account has been closed!\n')
                break
            elif user_input == 5:
                print('\nYou have successfully logged out!\n')
                break
            elif user_input == 0:
                self.connection.close()
                print('\nBye!')
                exit()
            else:
                print('Wrong input\n')
                continue

    def do_transfer(self, user):
        print('\nTransfer', 'Enter card number:', sep='\n')
        receiver_card = input()
        if receiver_card == user.card:
            return "You can't transfer money to the same account!"

        if not self.check_luhn(receiver_card):
            return "Probably you made a mistake in the card number. Please try again!\n"

        self.cursor.execute(f'SELECT * FROM card where number="{receiver_card}"')
        get_receiver = self.cursor.fetchone()
        if not get_receiver:
            return "Such a card does not exist."

        print("Enter how much money you want to transfer:")
        money_to_transfer = int(input())
        if money_to_transfer > user.balance:
            return "Not enough money!"

        receiver = BankAccount(*get_receiver)
        user.balance -= money_to_transfer
        receiver.balance += money_to_transfer

        self.cursor.execute('UPDATE card SET balance = ? WHERE id = ?;', (user.balance, user.id))
        self.cursor.execute('UPDATE card SET balance = ? WHERE id = ?;', (receiver.balance, receiver.id))
        self.connection.commit()
        return 'Success!'

    @staticmethod
    def check_luhn(card) -> bool:
        return card[-1] == BankAccount.luhn(card[:-1])


my_bank = ABS('card.s3db')
my_bank.main()