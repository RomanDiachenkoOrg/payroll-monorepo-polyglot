const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function validateLogin({ email, password }) {
  const errors = {};
  if (!email?.trim()) errors.email = "Email is required";
  else if (!EMAIL_RE.test(email.trim())) errors.email = "Enter a valid email address";
  if (!password) errors.password = "Password is required";
  return errors;
}

export function validateEmployee(e, today = new Date().toISOString().slice(0, 10)) {
  const errors = {};
  if (!e.firstName?.trim()) errors.firstName = "First name is required";
  if (!e.lastName?.trim()) errors.lastName = "Last name is required";
  if (!e.email?.trim()) errors.email = "Email is required";
  else if (!EMAIL_RE.test(e.email.trim())) errors.email = "Enter a valid email address";
  if (!e.title?.trim()) errors.title = "Job title is required";
  if (!e.departmentId) errors.departmentId = "Department is required";
  if (!e.hireDate) errors.hireDate = "Hire date is required";
  else if (e.hireDate > today) errors.hireDate = "Hire date cannot be in the future";
  if (e.payType === "SALARIED" && !(Number(e.annualSalary) > 0)) errors.annualSalary = "Salary must be greater than 0";
  if (e.payType === "HOURLY" && !(Number(e.hourlyRate) > 0)) errors.hourlyRate = "Hourly rate must be greater than 0";
  return errors;
}

export function validateHours(hours) {
  if (!Array.isArray(hours) || hours.length !== 7) return "A week has 7 days";
  for (const h of hours) {
    const n = Number(h);
    if (h === "" || h === null || Number.isNaN(n) || n < 0 || n > 24) return "Hours per day must be between 0 and 24";
  }
  return null;
}

export function validateDepartment({ name, code }) {
  const errors = {};
  if (!name || name.trim().length < 2) errors.name = "Name must have at least 2 characters";
  if (!/^[A-Za-z]{2,6}$/.test(code?.trim() ?? "")) errors.code = "Code must be 2-6 letters";
  return errors;
}
