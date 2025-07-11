import requests
import os
import json
import time

BASE_URL = "http://127.0.0.1:8000"
API_V1_URL = f"{BASE_URL}/api/v1"
TEST_USER = {"username": "testuser_profiling", "password": "password123"}
ACCESS_TOKEN = ""

# Path to a sample CSV file. Create one if it doesn't exist.
CSV_FILE_PATH = "sample_for_profiling.csv"
CSV_CONTENT = """col1,col2,col3
1,a,x
2,b,y
3,c,z
4,d,a
5,e,b
"""

def diagnose_routes():
    """Fetches and prints all registered routes from the server's OpenAPI schema."""
    print("--- Running Route Diagnostics ---")
    try:
        response = requests.get(f"{BASE_URL}/openapi.json")
        if response.status_code == 200:
            schema = response.json()
            paths = schema.get("paths", {})
            print("Server has the following routes registered:")
            for path, methods in paths.items():
                print(f"- {path}")
                for method in methods.keys():
                    print(f"  - {method.upper()}")
            if not paths:
                print("No paths found in OpenAPI schema.")
        else:
            print(f"Could not fetch OpenAPI schema. Status: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        print(f"Failed to connect to the server to diagnose routes: {e}")
    print("--- Route Diagnostics Finished ---")

def create_sample_csv():
    """Creates a sample CSV file for testing."""
    if not os.path.exists(CSV_FILE_PATH):
        with open(CSV_FILE_PATH, "w") as f:
            f.write(CSV_CONTENT)
    print(f"Sample CSV '{CSV_FILE_PATH}' is ready.")

def register_and_login():
    """Registers a new user (if not exists) and logs in to get an access token."""
    global ACCESS_TOKEN
    
    try:
        register_response = requests.post(
            f"{API_V1_URL}/users/", 
            json={"username": TEST_USER["username"], "email": f"{TEST_USER['username']}@example.com", "password": TEST_USER["password"]}
        )
        if register_response.status_code == 201:
            print(f"User '{TEST_USER['username']}' registered successfully.")
        elif register_response.status_code == 400 and "already registered" in register_response.text:
            print(f"User '{TEST_USER['username']}' already exists, proceeding to login.")
        else:
            print(f"Unexpected error during registration: {register_response.status_code} {register_response.text}")

    except requests.exceptions.RequestException as e:
        print(f"Could not connect to the server to register user: {e}")
        return False

    try:
        login_response = requests.post(f"{API_V1_URL}/auth/token", data=TEST_USER)
        if login_response.status_code == 200:
            ACCESS_TOKEN = login_response.json()["access_token"]
            print("Login successful.")
            return True
        else:
            print(f"Login failed: {login_response.status_code} {login_response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"Could not connect to the server to log in: {e}")
        return False


def create_project():
    """Creates a new project for the logged-in user."""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    project_data = {"name": "Profiling Test Project", "description": "A project for testing data profiling"}
    response = requests.post(f"{API_V1_URL}/projects/", headers=headers, json=project_data)
    
    if response.status_code in [200, 201]:
        project_id = response.json()["id"]
        print(f"Project created with ID: {project_id}")
        return project_id
    else:
        print(f"Failed to create project: {response.status_code} {response.text}")
        return None

def upload_data_source(project_id):
    """Uploads the sample CSV as a data source to the created project."""
    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    url = f"{API_V1_URL}/projects/{project_id}/datasources/upload"
    try:
        with open(CSV_FILE_PATH, 'rb') as f:
            files = {'file': (os.path.basename(CSV_FILE_PATH), f, 'text/csv')}
            data = {'name': 'Sample CSV for Profiling', 'description': 'A test CSV file'}
            
            response = requests.post(url, headers=headers, files=files, data=data)

        if response.status_code in [200, 201]:
            data_source = response.json()
            data_source_id = data_source["id"]
            print(f"Data source uploaded successfully. ID: {data_source_id}, Path: {data_source.get('file_path')}")
            return data_source_id
        else:
            print(f"Failed to upload data source: {response.status_code} {response.text}")
            return None
    except FileNotFoundError:
        print(f"Error: Test file '{CSV_FILE_PATH}' not found.")
        return None


def run_profiling(data_source_id):
    """Triggers the profiling process for the given data source."""
    if not data_source_id:
        print("Cannot run profiling without a valid data_source_id.")
        return

    headers = {"Authorization": f"Bearer {ACCESS_TOKEN}"}
    url = f"{API_V1_URL}/processing/profile/{data_source_id}"
    print(f"Requesting profiling for data source ID: {data_source_id} at {url}")
    
    try:
        response = requests.post(url, headers=headers, timeout=120)

        if response.status_code == 200:
            print("Profiling request successful.")
            result = response.json()
            print("Profiling Result:", json.dumps(result, indent=2))
            assert "report_html_path" in result
            print("✅ Test Passed: Profiling endpoint returned a valid and successful response.")
        else:
            print(f"❌ Test Failed: Profiling request failed with status {response.status_code}")
            print("Response content:", response.text)

    except requests.exceptions.RequestException as e:
        print(f"❌ Test Failed: An error occurred during the request: {e}")


def cleanup():
    """Removes the sample CSV file."""
    if os.path.exists(CSV_FILE_PATH):
        os.remove(CSV_FILE_PATH)
        print(f"Cleaned up {CSV_FILE_PATH}")


def main():
    """Main test execution function."""
    print("--- Starting Profiling API Test ---")
    diagnose_routes()
    time.sleep(2)

    create_sample_csv()
    if register_and_login():
        project_id = create_project()
        if project_id:
            data_source_id = upload_data_source(project_id)
            if data_source_id:
                run_profiling(data_source_id)

    print("--- Test Finished ---")
    cleanup()


if __name__ == "__main__":
    main() 