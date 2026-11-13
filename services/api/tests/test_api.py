from tests.conftest import login


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok"}


def test_login_validation_and_wrong_password(client):
    res = client.post("/api/auth/login", json={"email": "nope", "password": ""})
    assert res.status_code == 422
    assert "email" in res.json()["fieldErrors"]
    res = client.post("/api/auth/login", json={"email": "admin@acme.test", "password": "wrong"})
    assert res.status_code == 401
    assert res.json()["message"] == "Invalid email or password"


def test_employee_list_filters_and_paging(client):
    h = login(client, "admin@acme.test")
    res = client.get("/api/employees", params={"status": "ALL", "pageSize": 10}, headers=h).json()
    assert res["total"] == 25
    assert res["totalPages"] == 3
    inactive = client.get("/api/employees", params={"status": "INACTIVE"}, headers=h).json()
    assert inactive["total"] == 3


def test_create_employee_validation(client):
    h = login(client, "admin@acme.test")
    body = {
        "firstName": "Jane",
        "lastName": "Doe",
        "email": "manager@acme.test",
        "title": "Analyst",
        "departmentId": 1,
        "payType": "SALARIED",
        "annualSalary": 50000,
        "hireDate": "2024-01-02",
    }
    res = client.post("/api/employees", json=body, headers=h)
    assert res.status_code == 409
    body["email"] = "jane.doe@acme.test"
    res = client.post("/api/employees", json={**body, "hireDate": "2999-01-01"}, headers=h)
    assert res.status_code == 422
    res = client.post("/api/employees", json=body, headers=h)
    assert res.status_code == 201


def test_department_with_active_employees_cannot_be_deleted(client):
    h = login(client, "admin@acme.test")
    res = client.delete("/api/departments/1", headers=h)
    assert res.status_code == 409
    assert "active employees" in res.json()["message"]


def test_employee_cannot_list_employees(client):
    h = login(client, "employee@acme.test")
    assert client.get("/api/employees", headers=h).status_code == 403
    assert client.get("/api/me/payslips", headers=h).status_code == 200


def test_pay_run_lifecycle(client):
    h = login(client, "admin@acme.test")
    runs = client.get("/api/payruns", headers=h).json()
    draft = next(r for r in runs if r["status"] == "DRAFT")
    paid = next(r for r in runs if r["status"] == "PAID")
    assert client.post(f"/api/payruns/{paid['id']}/calculate", headers=h).status_code == 409
    res = client.post(f"/api/payruns/{draft['id']}/calculate", headers=h)
    assert res.status_code == 200
    assert res.json()["status"] == "CALCULATED"
    assert client.post(f"/api/payruns/{draft['id']}/pay", headers=h).status_code == 409
    assert client.post(f"/api/payruns/{draft['id']}/approve", headers=h).json()["status"] == "APPROVED"
    assert client.post(f"/api/payruns/{draft['id']}/pay", headers=h).json()["status"] == "PAID"


def test_manager_rejects_submitted_timesheet(client):
    h = login(client, "manager@acme.test")
    submitted = client.get("/api/timesheets", params={"status": "SUBMITTED"}, headers=h).json()
    assert submitted
    ts = submitted[0]
    assert client.post(f"/api/timesheets/{ts['id']}/reject", json={"reason": "no"}, headers=h).status_code == 422
    res = client.post(f"/api/timesheets/{ts['id']}/reject", json={"reason": "Missing ticket reference"}, headers=h)
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"
