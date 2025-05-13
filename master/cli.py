#!/usr/bin/env python
import os
import sys
import time
import json
import requests
from typing import List, Dict, Optional, Any

DEFAULT_API_HOST = os.environ.get("DEFAULT_IP", "127.0.0.1")
DEFAULT_API_PORT = int(os.environ.get("DEFAULT_PORT", 5000))
API_BASE_URL = f"http://{DEFAULT_API_HOST}:{DEFAULT_API_PORT}"

class MasterCrackerCLI:
    def __init__(self):
        self.api_base_url = API_BASE_URL
        self.running = True
        print(f"Connecting to Master Cracker API at: {self.api_base_url}")
        self._check_api_connection()

    def _check_api_connection(self):
        """Check if the API server is running and accessible"""
        retry_count = 0
        max_retries = 5
        
        while retry_count < max_retries:
            try:
                print(f"Checking API connection (attempt {retry_count+1}/{max_retries})...")
                # Try to access the minions status endpoint as a basic health check
                response = requests.get(f"{self.api_base_url}/get-minions-status", timeout=2)
                if response.status_code == 200:
                    print("✅ Successfully connected to Master Cracker API")
                    return True
            except requests.RequestException:
                pass
            
            retry_count += 1
            if retry_count < max_retries:
                print(f"Connection failed. Retrying in 3 seconds...")
                time.sleep(3)
        
        print("❌ Failed to connect to the Master Cracker API.")
        print(f"Please ensure the API server is running at {self.api_base_url}")
        return False

    def display_menu(self):
        """Display the main menu options"""
        print("\n" + "="*50)
        print("   MASTER PASSWORD CRACKER - COMMAND CENTER")
        print("="*50)
        print("1. Add New Minion")
        print("2. View Minions Status")
        print("3. Add New Hashes to Crack")
        print("4. Monitor Hash Status (Live)")
        print("5. Exit")
        print("="*50)

    def handle_add_minion(self):
        """Add a new minion to the cracking network"""
        print("\n--- Add New Minion ---")
        
        ip = input("Enter Minion IP address: ").strip()
        if not ip:
            ip = "127.0.0.1"
            print(f"Using default IP: {ip}")
        
        try:
            port = int(input("Enter Minion port: ").strip())
        except ValueError:
            port = 5001
            print(f"Invalid port. Using default port: {port}")
        
        try:
            payload = {"Ip": ip, "Port": port}
            response = requests.post(f"{self.api_base_url}/add-minion", json=payload)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Successfully added minion with ID: {result['minion_id']}")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                print(f"\n❌ Failed to add minion: {error_msg}")
        
        except requests.RequestException as e:
            print(f"\n❌ Connection error: {e}")
        
        input("\nPress Enter to continue...")

    def handle_view_minions(self):
        """View all registered minions and their status"""
        print("\n--- Minions Status ---")
        
        try:
            response = requests.get(f"{self.api_base_url}/get-minions-status")
            
            if response.status_code == 200:
                minions = response.json()
                
                if not minions:
                    print("No minions registered yet.")
                else:
                    # Print table header
                    print(f"{'ID':<5} {'IP':<15} {'Port':<6} {'Status':<12} {'Last Seen':<20}")
                    print("-" * 60)
                    
                    for minion in minions:
                        print(f"{minion['Id']:<5} {minion['Ip']:<15} {minion['Port']:<6} {minion['Status']:<12} {minion['LastSeen']:<20}")
            else:
                print(f"❌ Failed to retrieve minions status: {response.text}")
        
        except requests.RequestException as e:
            print(f"❌ Connection error: {e}")
        
        input("\nPress Enter to continue...")

    def handle_add_hashes(self):
        """Add new hashes to be cracked"""
        print("\n--- Add New Hashes to Crack ---")
        
        print("Select input method:")
        print("1. Enter hashes manually")
        print("2. Load hashes from file")
        
        choice = input("Enter your choice (1-2): ").strip()
        
        hashes = []
        
        if choice == '1':
            # Manual hash entry
            print("Enter MD5 hashes to crack, one per line.")
            print("Leave a blank line when finished.")
            
            while True:
                hash_input = input("> ").strip()
                if not hash_input:
                    break
                
                # Basic validation for MD5 hash format (32 hex chars)
                if len(hash_input) == 32 and all(c in "0123456789abcdefABCDEF" for c in hash_input):
                    hashes.append(hash_input)
                else:
                    print("⚠️  Invalid MD5 hash format. Must be 32 hexadecimal characters.")
        
        elif choice == '2':
            # File input
            file_path = input("Enter path to file containing MD5 hashes (one per line): ").strip()
            
            if not file_path:
                print("No file path provided.")
                input("\nPress Enter to continue...")
                return
            
            try:
                with open(file_path, 'r') as file:
                    line_number = 0
                    valid_count = 0
                    invalid_count = 0
                    
                    for line in file:
                        line_number += 1
                        hash_input = line.strip()
                        
                        if not hash_input:  # Skip empty lines
                            continue
                        
                        # Basic validation for MD5 hash format (32 hex chars)
                        if len(hash_input) == 32 and all(c in "0123456789abcdefABCDEF" for c in hash_input):
                            hashes.append(hash_input)
                            valid_count += 1
                        else:
                            invalid_count += 1
                            print(f"⚠️  Line {line_number}: Invalid MD5 hash format: {hash_input}")
                    
                    print(f"\nFound {valid_count} valid hashes and {invalid_count} invalid entries.")
            
            except FileNotFoundError:
                print(f"❌ File not found: {file_path}")
                input("\nPress Enter to continue...")
                return
            except PermissionError:
                print(f"❌ Permission denied: {file_path}")
                input("\nPress Enter to continue...")
                return
            except Exception as e:
                print(f"❌ Error reading file: {e}")
                input("\nPress Enter to continue...")
                return
        
        else:
            print("⚠️  Invalid choice.")
            input("\nPress Enter to continue...")
            return
        
        if not hashes:
            print("No valid hashes provided.")
            input("\nPress Enter to continue...")
            return
        
        try:
            response = requests.post(f"{self.api_base_url}/add-new-hashes", json=hashes)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✅ Added {result['hashes_added']} new hashes")
                print(f"✅ Created {result['jobs_created']} crack jobs")
            else:
                error_msg = response.json().get("detail", "Unknown error")
                print(f"\n❌ Failed to add hashes: {error_msg}")
        
        except requests.RequestException as e:
            print(f"\n❌ Connection error: {e}")
        
        input("\nPress Enter to continue...")

    def handle_monitor_hashes(self):
        """Monitor hash status in real-time with auto-refresh"""
        import platform
        import sys
        
        # Platform-specific imports for non-blocking keyboard input
        if platform.system() == 'Windows':
            import msvcrt
        else:  # For Linux and macOS
            import select
            import termios
            import tty
            
            # Set up terminal for non-blocking input on Unix-like systems
            def setup_terminal():
                old_settings = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin.fileno())
                return old_settings
                
            def restore_terminal(old_settings):
                termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
                
            # Check if a key was pressed on Unix-like systems
            def kbhit():
                dr, dw, de = select.select([sys.stdin], [], [], 0)
                return dr != []
                
            # Get the pressed key on Unix-like systems
            def getch():
                return sys.stdin.read(1)

        print("\n--- Live Hash Status Monitor ---")
        print("Monitoring hash status. Press 'q' to stop...")

        # Set up the terminal for Unix-like systems
        old_settings = None
        if platform.system() != 'Windows':
            try:
                old_settings = setup_terminal()
            except:
                print("Warning: Unable to configure terminal. Ctrl+C will be required to exit.")

        try:
            refresh_interval = 5  # Refresh every 5 seconds

            # Clear the screen based on OS
            os.system('cls' if os.name == 'nt' else 'clear')

            last_update_time = time.time() - refresh_interval  # Force immediate first update

            while True:
                current_time = time.time()
                
                # Check if 'q' key was pressed to exit - platform specific implementation
                if platform.system() == 'Windows':
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                        if key == 'q':
                            print("\nStopped monitoring. Returning to main menu...")
                            time.sleep(1)  # Give user a moment to see the message
                            return
                else:  # Linux and macOS
                    try:
                        if kbhit():
                            key = getch().lower()
                            if key == 'q':
                                print("\nStopped monitoring. Returning to main menu...")
                                time.sleep(1)  # Give user a moment to see the message
                                return
                    except:
                        pass  # Silently fail if keyboard input detection has issues

                # Only refresh data when interval has passed
                if current_time - last_update_time >= refresh_interval:
                    try:
                        response = requests.get(f"{self.api_base_url}/get-hash-reports")

                        if response.status_code == 200:
                            hash_reports = response.json()

                            # Clear screen before redrawing
                            os.system('cls' if os.name == 'nt' else 'clear')

                            print("\n" + "="*85)
                            print(" "*30 + "HASH STATUS MONITOR")
                            print("="*85)

                            if not hash_reports:
                                print("No hashes found in the system.")
                            else:
                                # Print table header
                                print(f"{'ID':<5} {'Hash Value':<34} {'Status':<10} {'Password':<15} {'Progress':<15}")
                                print("-" * 85)

                                for report in hash_reports:
                                    hash_id = report.get('hash_id', 'N/A')
                                    hash_value = report.get('hash_value', 'N/A')
                                    status = report.get('status', 'Unknown')
                                    password = report.get('password', '') or 'Not found'

                                    # Calculate progress for uncracked hashes
                                    progress = "N/A"
                                    if status != 'Cracked' and report.get('total_jobs') is not None:
                                        total = report.get('total_jobs', 0)
                                        completed = report.get('completed_jobs', 0)
                                        if total > 0:
                                            percentage = (completed / total) * 100
                                            progress = f"{completed}/{total} ({percentage:.1f}%)"

                                    print(f"{hash_id:<5} {hash_value:<34} {status:<10} {password:<15} {progress:<15}")

                            print("\n" + "="*85)
                            print(f"Auto-refreshing every {refresh_interval} seconds. Press 'q' to exit.")
                            print("="*85)
                        else:
                            print(f"❌ Failed to retrieve hash status: {response.text}")

                    except requests.RequestException as e:
                        print(f"❌ Connection error: {e}")
                    
                    last_update_time = current_time

                # Sleep a short amount to prevent excessive CPU usage
                # but still maintain responsiveness to keyboard input
                time.sleep(0.1)

        except KeyboardInterrupt:
            print("\nStopped monitoring. Returning to main menu...")
            time.sleep(1)  # Give user a moment to see the message

        except Exception as e:
            print(f"\nUnexpected error: {e}")
            input("\nPress Enter to return to the main menu...")
            
        finally:
            # Restore terminal settings on Unix-like systems
            if platform.system() != 'Windows' and old_settings:
                try:
                    restore_terminal(old_settings)
                except:
                    pass

    def run(self):
        """Main CLI loop"""
        while self.running:
            self.display_menu()
            choice = input("Enter your choice (1-5): ")
            
            if choice == '1':
                self.handle_add_minion()
            elif choice == '2':
                self.handle_view_minions()
            elif choice == '3':
                self.handle_add_hashes()
            elif choice == '4':
                self.handle_monitor_hashes()
            elif choice == '5':
                print("\nExiting Master Cracker CLI. Goodbye!")
                self.running = False
            else:
                print("\n⚠️  Invalid choice. Please select a number between 1 and 5.")

def main():
    print("Starting Master Password Cracker CLI...")
    cli = MasterCrackerCLI()
    cli.run()

if __name__ == "__main__":
    main()