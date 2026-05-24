import { useAuth } from '../context/AuthContext';

export function ProfilePage() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div className="page">
      <h2>Profile</h2>
      <p className="muted">Your HR account and linked employee record.</p>

      <div className="card">
        <h3>Account</h3>
        <dl className="detail-list">
          <div>
            <dt>Email</dt>
            <dd>{user.email}</dd>
          </div>
          <div>
            <dt>Name</dt>
            <dd>
              {user.first_name} {user.last_name}
            </dd>
          </div>
        </dl>
      </div>

      <div className="card">
        <h3>Linked employee</h3>
        {user.employee ? (
          <dl className="detail-list">
            <div>
              <dt>Employee ID</dt>
              <dd>{user.employee.id}</dd>
            </div>
            <div>
              <dt>Job title</dt>
              <dd>{user.employee.job_title}</dd>
            </div>
            <div>
              <dt>Department</dt>
              <dd>{user.employee.department}</dd>
            </div>
            <div>
              <dt>Country</dt>
              <dd>{user.employee.country}</dd>
            </div>
          </dl>
        ) : (
          <p className="muted">No employee record linked to this account.</p>
        )}
      </div>
    </div>
  );
}
