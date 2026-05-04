# 🧪 End-to-End Testing Guide — CertifyMe Admin Portal

**Objective**: Manually verify all user stories work correctly from signup → login → opportunity management → logout

**Duration**: ~15-20 minutes  
**Requirements**: Terminal + 2 Browser windows (Backend + Frontend)

---

## 📋 PRE-TESTING CHECKLIST

Before starting, verify your environment:

- [ ] Python 3.12+ installed: `python3 --version`
- [ ] `uv` package manager installed: `uv --version`
- [ ] Project dependencies installed: `uv sync`
- [ ] Fresh database: Delete `instance/app.db` if you want clean start
- [ ] `.env` file exists with SECRET_KEY and DATABASE_URL

---

## 🚀 STEP 0: START SERVERS (2 terminals)

### Terminal 1: Backend Flask Server

```bash
cd /Users/pankajraikar/Desktop/projects/github/certifyme-web
uv run flask --app run.py db upgrade
uv run flask --app run.py run --port 5000
```

**Expected Output:**

```
Running on http://127.0.0.1:5000
Press CTRL+C to quit
 * Restarting with reloader
 * Debugger is active!
```

**✅ Backend running on port 5000**

### Terminal 2: Frontend Server (Live Server)

```bash
cd /Users/pankajraikar/Desktop/projects/github/certifyme-web
# Open sky/admin.html with Live Server plugin in VS Code
# OR use Python simple HTTP server:
python3 -m http.server 5500 --directory sky
```

**Expected Output:**

```
Serving HTTP on 0.0.0.0 port 5500 (http://0.0.0.0:5500/) ...
```

**✅ Frontend running on port 5500**

---

## 🧪 TEST 1: SIGNUP (User Story US-1.1)

### Test Case 1.1: Valid Signup with New Email

**Setup**: Open browser → `http://127.0.0.1:5500/admin.html`

**Action Steps**:

1. **You should see**: Login form with fields:
   - Email
   - Password
   - Remember Me checkbox
   - Link: "Don't have an account? Create one"

2. **Click**: "Create one" link (or click the Signup tab)

3. **You should see**: Signup form with fields:
   - Full Name
   - Email
   - Password
   - Confirm Password
   - Signup button

4. **Fill form**:

   ```
   Full Name: John Doe
   Email: john.doe@example.com
   Password: MyPassword123
   Confirm Password: MyPassword123
   ```

5. **Click**: Signup button

6. **Expected Result**:
   - ✅ Form submits successfully
   - ✅ Toast notification: "Account created successfully!"
   - ✅ Redirects to Login page (not dashboard yet)
   - ✅ Can log in with these credentials

**Verify in Backend (Terminal 1)**:

```bash
# Should see in Flask debug logs:
# POST /api/auth/signup - 201 Created
# No errors in backend terminal
```

---

### Test Case 1.2: Validation — Missing Full Name

**Fill form**:

```
Full Name: [EMPTY]
Email: test2@example.com
Password: MyPassword123
Confirm Password: MyPassword123
```

**Click**: Signup button

**Expected Result**:

- ✅ Form does NOT submit
- ✅ Error message shows: "Full name is required"
- ✅ Toast shows validation error

---

### Test Case 1.3: Validation — Invalid Email Format

**Fill form**:

```
Full Name: Jane Doe
Email: notanemail
Password: MyPassword123
Confirm Password: MyPassword123
```

**Click**: Signup button

**Expected Result**:

- ✅ Form does NOT submit
- ✅ Error message shows: "Invalid email format"
- ✅ Toast shows validation error

---

### Test Case 1.4: Validation — Short Password

**Fill form**:

```
Full Name: Bob Smith
Email: bob@example.com
Password: Short1
Confirm Password: Short1
```

**Click**: Signup button

**Expected Result**:

- ✅ Form does NOT submit
- ✅ Error message shows: "Password must be at least 8 characters"
- ✅ Toast shows validation error

---

### Test Case 1.5: Validation — Passwords Don't Match

**Fill form**:

```
Full Name: Alice Brown
Email: alice@example.com
Password: MyPassword123
Confirm Password: DifferentPassword123
```

**Click**: Signup button

**Expected Result**:

- ✅ Form does NOT submit
- ✅ Error message shows: "Passwords do not match"
- ✅ Toast shows validation error

---

### Test Case 1.6: Error — Duplicate Email

**Setup**: Use email from Test 1.1 (john.doe@example.com)

**Fill form**:

```
Full Name: John Duplicate
Email: john.doe@example.com
Password: MyPassword123
Confirm Password: MyPassword123
```

**Click**: Signup button

**Expected Result**:

- ✅ Form does NOT submit
- ✅ Toast notification: "Email already registered. Please login or use a different email."
- ✅ HTTP 409 error in backend
- ✅ Remains on signup form

---

## 🔐 TEST 2: LOGIN (User Story US-1.2)

### Test Case 2.1: Valid Login

**Setup**: You should be on Login page from signup

**Action Steps**:

1. **You should see**: Login form with fields:
   - Email
   - Password
   - Remember Me checkbox
   - Login button

2. **Fill form** with credentials from Test 1.1:

   ```
   Email: john.doe@example.com
   Password: MyPassword123
   Remember Me: [UNCHECKED]
   ```

3. **Click**: Login button

4. **Expected Result**:
   - ✅ Form submits successfully
   - ✅ Toast notification: "Login successful!"
   - ✅ Redirects to Dashboard
   - ✅ You should see personalized greeting: "Hello, John Doe!" (or user's name)
   - ✅ Dashboard shows "Opportunity Management" section (empty initially)
   - ✅ Session cookie set in browser

**Verify in Backend (Terminal 1)**:

```bash
# Should see:
# POST /api/auth/login - 200 OK
# GET /api/opportunities - 200 OK
```

**Verify in Browser DevTools**:

- Open DevTools (F12) → Application → Cookies
- You should see: `session` cookie with HTTPONLY flag
- Copy this cookie value to use later

---

### Test Case 2.2: Invalid Email

**On Login page, fill form**:

```
Email: nonexistent@example.com
Password: MyPassword123
```

**Click**: Login button

**Expected Result**:

- ✅ Form does NOT submit to dashboard
- ✅ Toast notification: "Invalid email or password"
- ✅ Note: Generic message (doesn't reveal if email exists)
- ✅ Stays on login form

---

### Test Case 2.3: Invalid Password

**Fill form**:

```
Email: john.doe@example.com
Password: WrongPassword123
```

**Click**: Login button

**Expected Result**:

- ✅ Form does NOT submit
- ✅ Toast notification: "Invalid email or password"
- ✅ Note: Same generic message (privacy protection)
- ✅ Stays on login form

---

### Test Case 2.4: Remember Me Functionality

**Fill form**:

```
Email: john.doe@example.com
Password: MyPassword123
Remember Me: [CHECKED]
```

**Click**: Login button

**Expected Result**:

- ✅ Redirects to Dashboard (same as Test 2.1)
- ✅ Session extended to 30 days

**Verify Duration**:

- DevTools → Application → Cookies → session
- Check the `Expires/Max-Age` attribute
- Should be ~30 days from now (not just session expiry)

---

## 📝 TEST 3: OPPORTUNITY MANAGEMENT (User Stories US-2.1 to US-2.6)

### 🎯 TEST 3.1: View All Opportunities (US-2.1)

**Setup**: You should be logged in as John Doe

**Current State**:

- ✅ Dashboard shows: "Opportunity Management" tab
- ✅ Grid area should be empty (no opportunities yet)
- ✅ Empty state displayed

**Verify**:

- ✅ No hardcoded opportunities visible
- ✅ Database is the source (not localStorage)

---

### ✨ TEST 3.2: Create New Opportunity (US-2.2)

**Setup**: On Dashboard with empty opportunities

**Action Steps**:

1. **Click Button**: "Add New Opportunity" (or "Create" button)

2. **You should see**: Modal form with fields:
   - Name (required)
   - Duration (required)
   - Start Date (required)
   - Description (required)
   - Skills (required) — comma-separated tags
   - Category (required) — dropdown
   - Future Opportunities (required) — text field
   - Max Applicants (optional) — number field
   - Submit & Cancel buttons

3. **Fill form with**:

   ```
   Name: Advanced React Development
   Duration: 12 weeks
   Start Date: 2026-06-01
   Description: Learn advanced React patterns, hooks, performance optimization
   Skills: React, JavaScript, TypeScript, Performance
   Category: Technology
   Future Opportunities: Graduates can pursue roles as Full Stack Developers, Frontend Developers, Backend Developers, or Software Engineers at top tech companies
   Max Applicants: 30
   ```

4. **Click**: Submit button

5. **Expected Result**:
   - ✅ Modal closes
   - ✅ Toast notification: "Opportunity created successfully!"
   - ✅ New opportunity appears as card in grid:
     - Card title: "Advanced React Development"
     - Category badge: "Technology"
     - Duration: "12 weeks"
     - Start Date: "2026-06-01"
     - Description text visible
     - Skills tags displayed: React, JavaScript, TypeScript, Performance
     - Three buttons: "View Details", "Edit", "Delete"

**Verify in Backend (Terminal 1)**:

```bash
# Should see:
# POST /api/opportunities - 201 Created
```

**Verify in Database**:

```bash
# Terminal, run:
sqlite3 instance/app.db "SELECT * FROM opportunities;"
# Should show one record with:
# - admin_id: 1 (John's ID)
# - name: "Advanced React Development"
# - category: "technology"
# - all other fields populated
```

---

### ✔️ TEST 3.3: Validation — Missing Required Field

**Click**: "Add New Opportunity" again

**Fill form** but leave Description empty:

```
Name: Python for Data Science
Duration: 8 weeks
Start Date: 2026-07-01
Description: [EMPTY]
Skills: Python, Pandas, NumPy
Category: Data
Future Opportunities: [CHECKED]
```

**Click**: Submit

**Expected Result**:

- ✅ Form does NOT submit
- ✅ Error message shown: "Description is required"
- ✅ Modal remains open for correction

---

### ✔️ TEST 3.4: Validation — Invalid Category

**Create opportunity via DevTools (to test backend validation)**:

```bash
# Terminal 3 (new):
curl -X POST http://127.0.0.1:5000/api/opportunities \
  -H "Content-Type: application/json" \
  -b cookies.txt \
  -d '{
    "name": "Invalid Category Test",
    "duration": "5 weeks",
    "start_date": "2026-08-01",
    "description": "Test description",
    "skills": "Test",
    "category": "invalidcategory",
    "future_opportunities": "Some future opportunity text"
  }'
```

**Expected Result**:

```json
{
  "error": "Invalid category. Must be one of: ...",
  "code": 422
}
```

- ✅ HTTP 422 Unprocessable Entity
- ✅ Error message clear
- ✅ Opportunity NOT created

---

### 👁️ TEST 3.5: View Opportunity Details (US-2.4)

**On Dashboard with card from Test 3.2**

**Click**: "View Details" button on "Advanced React Development" card

**You should see**: Modal showing all fields:

```
Title: Advanced React Development
Duration: 12 weeks
Start Date: 2026-06-01
Description: Learn advanced React patterns, hooks, performance optimization
Skills Tags: React | JavaScript | TypeScript | Performance
Category: Technology
Future Opportunities: Yes
Max Applicants: 30
```

**UI Elements**:

- ✅ All field values displayed correctly
- ✅ Skills shown as individual tags/badges
- ✅ Close button (X) in top-right corner
- ✅ "Apply to Opportunity" button (UI feature)

**Action**: Click close button or click outside modal

**Expected Result**:

- ✅ Modal closes
- ✅ Returns to dashboard
- ✅ Card still visible in grid

---

### ✏️ TEST 3.6: Edit Opportunity (US-2.5)

**On Dashboard with card from Test 3.2**

**Click**: "Edit" button on "Advanced React Development" card

**You should see**: Modal form with fields **PRE-POPULATED**:

```
Name: Advanced React Development (pre-filled)
Duration: 12 weeks (pre-filled)
Start Date: 2026-06-01 (pre-filled)
Description: Learn advanced React patterns... (pre-filled)
Skills: React, JavaScript, TypeScript, Performance (pre-filled)
Category: Technology (pre-filled)
Future Opportunities: Graduates can pursue roles as... (pre-filled)
Max Applicants: 30 (pre-filled)
```

**Modify fields**:

```
Name: Advanced React Development (add suffix) → Advanced React Development - Updated
Max Applicants: 30 → 50
Description: Learn advanced React patterns... → Learn advanced React patterns and best practices for production applications
```

**Click**: Submit

**Expected Result**:

- ✅ Modal closes
- ✅ Toast notification: "Opportunity updated successfully!"
- ✅ Card updates immediately with new values:
  - Title now shows: "Advanced React Development - Updated"
  - Description now shows updated text
  - Max Applicants changed to 50
- ✅ No page refresh needed

**Verify in Backend**:

```bash
# Terminal:
sqlite3 instance/app.db "SELECT name, max_applicants, description FROM opportunities WHERE id=1;"
# Should show updated values
```

---

### 🗑️ TEST 3.7: Delete Opportunity (US-2.6)

**On Dashboard**

**Click**: "Delete" button on "Advanced React Development - Updated" card

**You should see**: Confirmation dialog:

```
"Are you sure you want to delete this opportunity?"
[Cancel] [OK]
```

**Test Case 3.7.1: Confirm Delete**

**Click**: "OK" button

**Expected Result**:

- ✅ Dialog closes
- ✅ Toast notification: "Opportunity deleted successfully!"
- ✅ Card disappears from grid immediately (no page refresh)
- ✅ Grid is empty again

**Verify in Database**:

```bash
# Terminal:
sqlite3 instance/app.db "SELECT COUNT(*) FROM opportunities;"
# Should return: 0
```

---

### TEST 3.7.2: Cancel Delete

**Create another opportunity** (Test 3.2 steps):

```
Name: UI/UX Design Fundamentals
Duration: 6 weeks
Start Date: 2026-06-15
Description: Master design principles and tools
Skills: Figma, Design, Prototyping
Category: Design
Future Opportunities: Graduates can work as UI/UX Designers, Product Designers, Experience Designers at leading tech companies
```

**Click**: "Delete" button on this card

**Click**: "Cancel" button in confirmation dialog

**Expected Result**:

- ✅ Dialog closes
- ✅ No toast notification
- ✅ Card remains in grid (no deletion)
- ✅ Opportunity unchanged in database

---

## 👥 TEST 4: MULTI-ADMIN ISOLATION (US-2.3)

### Test Case 4.1: Create Second Admin and Verify Isolation

**Setup**: Open SECOND browser window (Incognito/Private)

**In Second Browser**:

1. **Navigate to**: `http://127.0.0.1:5500/admin.html`

2. **Create new account**:

   ```
   Full Name: Jane Smith
   Email: jane.smith@example.com
   Password: JanePassword456
   Confirm Password: JanePassword456
   ```

3. **Sign up** → Auto-redirects to Login page

4. **Login** with Jane's credentials

5. **You should see**: Dashboard with:
   - ✅ Empty opportunities grid
   - ✅ Personalized greeting: "Hello, Jane Smith!"
   - ✅ Jane CANNOT see John's opportunity ("UI/UX Design Fundamentals")

**Verify Isolation**:

- ✅ Jane's dashboard is empty
- ✅ John's opportunities hidden from Jane
- ✅ Each admin sees only own opportunities

---

### Test Case 4.2: Create Opportunity as Jane

**In Second Browser (Jane's session)**:

**Create opportunity**:

```
Name: Marketing Strategy Workshop
Duration: 4 weeks
Start Date: 2026-07-10
Description: Learn marketing fundamentals and strategies
Skills: Marketing, Strategy, Analytics
Category: Marketing
Future Opportunities: Career paths include Marketing Manager, Digital Marketing Specialist, Marketing Analyst, or Content Strategist
Max Applicants: 25
```

**Submit** → Opportunity appears

---

### Test Case 4.3: Verify John Doesn't See Jane's Opportunity

**Switch to First Browser (John's session)**

**Refresh Dashboard** or navigate back

**Expected Result**:

- ✅ John sees his own opportunity: "UI/UX Design Fundamentals"
- ✅ John does NOT see Jane's opportunity: "Marketing Strategy Workshop"
- ✅ Count: 1 opportunity (not 2)

---

### Test Case 4.4: Verify Cross-Admin Edit/Delete Fails

**In Jane's session**, use DevTools Console:

```javascript
// Try to edit John's opportunity directly (should fail with 404)
const res = await fetch("http://127.0.0.1:5000/api/opportunities/1", {
  method: "PUT",
  headers: { "Content-Type": "application/json" },
  credentials: "include",
  body: JSON.stringify({ name: "Hacked" }),
});
console.log(res.status); // Should be 404
```

**Expected Result**:

- ✅ HTTP 404 Not Found
- ✅ Jane cannot access John's opportunity via API
- ✅ Backend ownership check working

---

## 🔒 TEST 5: SECURITY FEATURES

### Test Case 5.1: Password Reset (US-1.3)

**On Login page**:

**Click**: "Forgot your password?" link

**You should see**: Form with:

- Email field
- Forgot Password button

**Fill**:

```
Email: john.doe@example.com
```

**Click**: Forgot Password button

**Expected Result**:

- ✅ Always shows: "If account exists, reset link sent to your email" (privacy message)
- ✅ HTTP 200 (no matter if email exists or not)

**Verify in Backend (Terminal 1)**:

```bash
# Should see console output like:
# Password reset requested for john.doe@example.com
# Reset link: http://127.0.0.1:5500/reset-password?token=...
```

---

### Test Case 5.2: Session Expiry (Security)

**Logged in as John**:

**Open DevTools → Network tab**

**Wait 2 minutes** and try to create opportunity

**Expected Behavior**:

- ✅ Session remains active (configured for 30 days by default)
- ✅ Opportunity creation still works

**To test ACTUAL session expiry** (optional):

- Modify `.env`: Set `PERMANENT_SESSION_LIFETIME=120` (2 minutes)
- Restart Flask
- Log in
- Wait 2+ minutes
- Try to create opportunity
- Should get 401 Unauthorized

---

### Test Case 5.3: HttpOnly Cookies (Security)

**In Browser DevTools** (Logged in):

```javascript
// Try to access session cookie from JavaScript (should fail)
console.log(document.cookie);
// Should show: "" (empty - HttpOnly prevents JavaScript access)
```

**Expected Result**:

- ✅ Output is empty string
- ✅ HttpOnly flag is working
- ✅ Cookies cannot be stolen via XSS

---

## 🚪 TEST 6: LOGOUT (User Story US-1.2)

### Test Case 6.1: Logout Button

**Logged in as John**:

**Click**: Logout button (in dashboard header/menu)

**Expected Result**:

- ✅ Session cleared
- ✅ Redirects to Login page
- ✅ Toast notification: "Logged out successfully!"
- ✅ Global state cleared (cannot see opportunities until re-login)

**Verify in DevTools**:

- ✅ Session cookie deleted/expired

---

### Test Case 6.2: Login After Logout

**On Login page** (after Test 6.1):

**Log in again** with John's credentials:

```
Email: john.doe@example.com
Password: MyPassword123
```

**Expected Result**:

- ✅ Login successful
- ✅ Dashboard shows John's opportunity: "UI/UX Design Fundamentals"
- ✅ Opportunity persisted in database across sessions
- ✅ No data lost

---

## 📊 TEST 7: COMPREHENSIVE SCENARIO

### Full User Journey Test

**Scenario**: Complete workflow from signup to opportunity management

**Test Steps**:

1. ✅ **Sign up** as new user
   - Fill all fields correctly
   - Verify 201 response
   - Redirects to Login

2. ✅ **Log in** with new account
   - Empty dashboard initially
   - Session cookie set
   - Remember Me works

3. ✅ **Create 3 opportunities**:
   - Opportunity A: Technology
   - Opportunity B: Design
   - Opportunity C: Marketing

4. ✅ **Edit Opportunity B**:
   - Change name, duration, description
   - Verify update in grid

5. ✅ **View Details** for each opportunity
   - All fields display correctly
   - Close modal works

6. ✅ **Delete Opportunity C**:
   - Confirm dialog appears
   - Opportunity removed from grid
   - Verify 2 opportunities remain

7. ✅ **Log out**
   - Session cleared
   - Redirected to Login

8. ✅ **Log in again**
   - Same 2 opportunities visible
   - Data persisted across sessions

9. ✅ **Open new browser, sign up as different user**:
   - New account works
   - Cannot see first user's opportunities
   - Can create own opportunities

10. ✅ **Verify isolation**:
    - First user still sees only own opportunities
    - Second user cannot modify first user's data

---

## ✅ FINAL VALIDATION CHECKLIST

### Authentication ✅

- [ ] Signup with valid data works (201)
- [ ] Signup validation works (422 for invalid input)
- [ ] Duplicate email prevention works (409)
- [ ] Login with correct credentials works (200)
- [ ] Login with wrong credentials shows generic error (401)
- [ ] Remember Me extends session
- [ ] Forgot password always returns 200 (privacy)
- [ ] Logout clears session
- [ ] Cannot access protected routes without login (401)

### Opportunity CRUD ✅

- [ ] Create opportunity works (201)
- [ ] List shows only own opportunities
- [ ] View details works
- [ ] Edit updates database (200)
- [ ] Delete removes from database (204)
- [ ] New opportunities appear without page refresh
- [ ] Form validation prevents invalid data

### Multi-Admin Isolation ✅

- [ ] Admin A cannot see Admin B's opportunities
- [ ] Admin A cannot edit Admin B's opportunities
- [ ] Admin A cannot delete Admin B's opportunities
- [ ] API returns 404 when accessing other admin's data
- [ ] Each admin sees personalized dashboard

### Data Persistence ✅

- [ ] Opportunities stored in database (not localStorage)
- [ ] Data persists across login/logout
- [ ] Data persists across browser refresh
- [ ] Deleted opportunities gone permanently

### Security ✅

- [ ] Passwords hashed (not plain text in DB)
- [ ] Generic error messages (no info leakage)
- [ ] Session cookies HttpOnly
- [ ] CORS working (backend port 5000, frontend port 5500)
- [ ] Credentials included in requests

### UI/UX ✅

- [ ] No hardcoded opportunities visible
- [ ] Form validation feedback clear
- [ ] Toast notifications for all actions
- [ ] Confirmation dialog for delete
- [ ] Modals close properly
- [ ] Grid updates immediately after CRUD

---

## 🐛 TROUBLESHOOTING

### Issue: "Backend not responding"

```bash
# Check if Flask is running:
lsof -i :5000
# If not, restart:
uv run flask --app run.py run --port 5000
```

### Issue: "CORS error" in browser console

```bash
# Verify CORS config in app/__init__.py
# Should have: cors = CORS(app, origins=["http://127.0.0.1:5500", ...])
# Restart Flask if changed
```

### Issue: "Database locked"

```bash
# Delete and reinitialize:
rm instance/app.db
uv run flask --app run.py db upgrade
```

### Issue: "Cannot create opportunity" (422 error)

```bash
# Check form validation:
# - All required fields filled?
# - Category is valid? (technology, business, design, marketing, data, other)
# - Date format correct? (YYYY-MM-DD)
```

### Issue: "Login returns 401"

```bash
# Verify credentials:
# - Email correct (case-insensitive)?
# - Password correct?
# - Account exists (check database):
sqlite3 instance/app.db "SELECT * FROM admins;"
```

---

## 📸 SCREENSHOTS TO CAPTURE

Optional: Take screenshots at each stage for documentation

- [ ] Signup form
- [ ] Login form with Remember Me
- [ ] Empty dashboard
- [ ] Opportunity grid with 3 cards
- [ ] Details modal
- [ ] Edit form with pre-populated data
- [ ] Delete confirmation dialog
- [ ] Multi-admin dashboard comparison

---

## ⏱️ TIME ESTIMATES

| Test                  | Duration       | Status |
| --------------------- | -------------- | ------ |
| Signup validation     | 3 min          | ⏳     |
| Login & session       | 2 min          | ⏳     |
| Create opportunity    | 2 min          | ⏳     |
| Edit opportunity      | 2 min          | ⏳     |
| Delete opportunity    | 1 min          | ⏳     |
| Multi-admin isolation | 3 min          | ⏳     |
| Forgot password       | 1 min          | ⏳     |
| Logout                | 1 min          | ⏳     |
| **TOTAL**             | **~15-20 min** | ⏳     |

---

## ✨ EXPECTED OUTCOMES

After completing all tests:

- ✅ All 9 user stories verified working
- ✅ All CRUD operations tested
- ✅ Multi-admin isolation confirmed
- ✅ Security features validated
- ✅ Data persistence confirmed
- ✅ Error handling working
- ✅ UI/UX smooth and responsive
- ✅ **Ready for production deployment**

---

**Good luck with testing! 🚀**

If any issues found, document them in GitHub issues and notify the development team.
