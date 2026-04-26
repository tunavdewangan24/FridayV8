import getpass
from friday_api_client import register, login, current_user, set_api_base, get_my_history, logout


def menu():
    print("\n=== FridayV8 Account Setup ===")
    print("1. Register new account")
    print("2. Login existing account")
    print("3. Show current logged-in user")
    print("4. Show my saved command history")
    print("5. Change API server URL")
    print("6. Logout")
    print("7. Exit")

    return input("Choose option: ").strip()


def main():
    while True:
        choice = menu()

        try:
            if choice == "1":
                name = input("Your name: ").strip()
                email = input("Email: ").strip()
                password = getpass.getpass("Create password: ")
                data = register(email=email, password=password, name=name)
                print(f"Registered and logged in as {data['email']} ({data['role']})")

            elif choice == "2":
                email = input("Email: ").strip()
                password = getpass.getpass("Password: ")
                data = login(email=email, password=password)
                print(f"Logged in as {data['email']} ({data['role']})")

            elif choice == "3":
                user = current_user()
                print(user if user else "Not logged in.")

            elif choice == "4":
                rows = get_my_history(limit=20)
                if not rows:
                    print("No history found.")
                for row in rows:
                    print(f"[{row['created_at']}] {row['command_text']} -> {row['status']}")

            elif choice == "5":
                url = input("API server URL, example http://127.0.0.1:8000: ").strip()
                set_api_base(url)
                print("API URL saved.")

            elif choice == "6":
                logout()
                print("Logged out.")

            elif choice == "7":
                break

            else:
                print("Invalid option.")

        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
