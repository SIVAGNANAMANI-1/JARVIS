import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useData } from '../../context/DataContext';
import {
  DollarSign, TrendingUp, CreditCard, Users,
  ArrowLeft, AlertTriangle, CalendarDays, ChevronDown, ChevronUp
} from 'lucide-react';
import './Dashboard.css';

const Dashboard = () => {
  const navigate = useNavigate();
  const { classes, students, fees, staff, calculateSalary } = useData();
  const now = new Date();
  const monthNum = now.getMonth() + 1;
  const yearNum = now.getFullYear();

  const [monthDropdownOpen, setMonthDropdownOpen] = useState(false);
  const [selectedMonth, setSelectedMonth] = useState(null);

  const currentMonth = now.toLocaleString('default', { month: 'long', year: 'numeric' });

  const academicStartYear = now.getMonth() >= 5 ? now.getFullYear() : now.getFullYear() - 1;
  const academicStart = new Date(academicStartYear, 5, 1);
  const curMonthStart = new Date(now.getFullYear(), now.getMonth(), 1);
  const pastMonths = [];
  const mIter = new Date(academicStart);
  while (mIter < curMonthStart) {
    pastMonths.push(mIter.toLocaleString('default', { month: 'long', year: 'numeric' }));
    mIter.setMonth(mIter.getMonth() + 1);
  }

  const allMonths = [...pastMonths, currentMonth].reverse();

  const getMonthStats = (m) => {
    let collected = 0;
    let expected = 0;
    students.filter(s => s.status !== 'past').forEach(s => {
      const cls = classes.find(c => c.id === s.classId);
      if (!cls) return;
      const fee = s.isScholarship && s.scholarshipFee != null ? s.scholarshipFee : (cls.defaultFee || 0);
      expected += fee;
      const rec = fees.find(f => f.studentId === s.id && f.month === m);
      if (rec) collected += Math.min(rec.amount ?? rec.amountPaid ?? 0, fee);
    });
    const pending = Math.max(0, expected - collected);
    const progress = expected > 0 ? Math.round((collected / expected) * 100) : 0;
    return { month: m, collected, expected, pending, progress };
  };

  const monthWiseIncome = allMonths.map(getMonthStats);
  const selectedMonthData = selectedMonth ? monthWiseIncome.find(m => m.month === selectedMonth) : null;

  const selectedMonthClassBreakdown = selectedMonth
    ? classes.map(c => {
        const cs = students.filter(s => s.classId === c.id && s.status !== 'past');
        let collected = 0;
        cs.forEach(s => {
          const fee = s.isScholarship && s.scholarshipFee != null ? s.scholarshipFee : (c.defaultFee || 0);
          const rec = fees.find(f => f.studentId === s.id && f.month === selectedMonth);
          if (rec) collected += Math.min(rec.amount ?? rec.amountPaid ?? 0, fee);
        });
        const expected = cs.reduce((sum, s) =>
          sum + (s.isScholarship && s.scholarshipFee != null ? s.scholarshipFee : (c.defaultFee || 0)), 0);
        return { name: c.name, collected, expected, pending: Math.max(0, expected - collected) };
      }).filter(c => c.expected > 0)
    : [];

  const backlogStudentCount = students.filter(s => {
    if (s.status === 'past') return false;
    const cls = classes.find(c => c.id === s.classId);
    if (!cls || !cls.defaultFee) return false;
    const fee = s.isScholarship && s.scholarshipFee != null ? s.scholarshipFee : cls.defaultFee;
    return pastMonths.some(m => {
      const rec = fees.find(f => f.studentId === s.id && f.month === m);
      if (!rec) return true;
      if ((rec.status || '').toLowerCase() === 'paid') return false;
      const paid = rec.amount ?? rec.amountPaid ?? 0;
      const balance = rec.balance > 0 ? rec.balance : Math.max(0, fee - paid);
      return balance > 0;
    });
  }).length;

  const totalFeesCollected = students.filter(s => s.status !== 'past').reduce((sum, s) => {
    const cls = classes.find(c => c.id === s.classId);
    if (!cls) return sum;
    const fee = s.isScholarship && s.scholarshipFee != null ? s.scholarshipFee : (cls.defaultFee || 0);
    const rec = fees.find(f => f.studentId === s.id && f.month === currentMonth);
    return sum + Math.min(rec ? (rec.amountPaid || rec.amount || 0) : 0, fee);
  }, 0);

  const totalExpected = students.filter(s => s.status !== 'past').reduce((sum, s) => {
    const cls = classes.find(c => c.id === s.classId);
    if (!cls) return sum;
    return sum + (s.isScholarship && s.scholarshipFee != null ? s.scholarshipFee : (cls.defaultFee || 0));
  }, 0);

  const totalPendingFees = Math.max(0, totalExpected - totalFeesCollected);
  const totalSalaryExpense = staff.reduce((sum, s) => sum + calculateSalary(s.id, monthNum, yearNum), 0);
  const netProfit = totalFeesCollected - totalSalaryExpense;

  const cards = [
    { title: 'Total Collected',    value: `\u20B9${totalFeesCollected}`, icon: DollarSign, type: 'revenue',    route: '/income/fee-status?tab=collected' },
    { title: 'Pending Collection', value: `\u20B9${totalPendingFees}`,   icon: CreditCard, type: 'pending',    route: '/income/fee-status?tab=pending'   },
    { title: 'Staff Salaries',     value: `\u20B9${totalSalaryExpense}`, icon: Users,      type: 'expense',    route: '/income/salaries'                  },
    { title: 'Net Income',         value: `\u20B9${netProfit}`,          icon: TrendingUp, type: netProfit >= 0 ? 'profit-pos' : 'profit-neg', route: null }
  ];

  const classBreakdown = classes.map(c => {
    const cs = students.filter(s => s.classId === c.id && s.status !== 'past');
    let collected = 0;
    cs.forEach(s => {
      const fee = s.isScholarship && s.scholarshipFee != null ? s.scholarshipFee : (c.defaultFee || 0);
      const rec = fees.find(f => f.studentId === s.id && f.month === currentMonth);
      collected += Math.min(rec ? (rec.amountPaid || rec.amount || 0) : 0, fee);
    });
    const expected = cs.reduce((sum, s) =>
      sum + (s.isScholarship && s.scholarshipFee != null ? s.scholarshipFee : (c.defaultFee || 0)), 0);
    const pending = Math.max(0, expected - collected);
    const progress = expected > 0 ? Math.round((collected / expected) * 100) : 0;
    return { id: c.id, name: c.name, studentCount: cs.length, collected, pending, expected, progress };
  });

  return (
    <div className="income-dashboard-container animate-fade-in">
      <header className="page-header sticky-header glass">
        <div className="header-top">
          <button onClick={() => navigate('/')} className="back-btn"><ArrowLeft size={20} /></button>
          <div className="header-title">
            <h1>Income Dashboard</h1>
            <p>Overall finances and class breakdown</p>
          </div>
        </div>
      </header>

      <div className="cards-grid">
        {cards.map((c, i) => {
          const Icon = c.icon;
          return (
            <div key={i}
              className={`card glass metric-card ${c.type} ${c.route ? 'clickable' : ''}`}
              onClick={c.route ? () => navigate(c.route) : undefined}>
              <div className="card-icon-container"><Icon size={22} /></div>
              <div className="card-content">
                <h3>{c.title}</h3>
                <p className="metric-value">{c.value}</p>
              </div>
            </div>
          );
        })}
      </div>

      <button className="backlogs-cta glass" onClick={() => navigate('/income/backlogs')}>
        <div className="backlogs-cta-left">
          <div className="backlogs-cta-icon"><AlertTriangle size={20} /></div>
          <div>
            <span className="backlogs-cta-title">Previous Month Backlogs</span>
            <span className="backlogs-cta-sub">
              {backlogStudentCount > 0
                ? `${backlogStudentCount} student${backlogStudentCount !== 1 ? 's' : ''} with unpaid dues`
                : 'No outstanding backlogs'}
            </span>
          </div>
        </div>
        {backlogStudentCount > 0 && <span className="backlogs-cta-badge">{backlogStudentCount}</span>}
      </button>

      <div className="monthwise-section">
        <button className="monthwise-btn glass"
          onClick={() => { setMonthDropdownOpen(o => !o); setSelectedMonth(null); }}>
          <div className="monthwise-btn-left">
            <div className="monthwise-icon"><CalendarDays size={20} /></div>
            <span className="monthwise-title">Month-wise Income</span>
          </div>
          {monthDropdownOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
        </button>

        {monthDropdownOpen && (
          <div className="monthwise-dropdown glass">
            <div className="mw-month-list">
              {monthWiseIncome.map(item => (
                <button key={item.month}
                  className={`mw-month-row ${selectedMonth === item.month ? 'active' : ''}`}
                  onClick={() => setSelectedMonth(selectedMonth === item.month ? null : item.month)}>
                  <div className="mw-month-left">
                    <span className="mw-month-name">{item.month}</span>
                    <div className="mw-progress-track">
                      <div className="mw-progress-fill" style={{ width: `${item.progress}%` }} />
                    </div>
                  </div>
                  <div className="mw-month-right">
                    <span className="mw-collected">{'\u20B9'}{item.collected.toLocaleString()}</span>
                    <span className="mw-pct">{item.progress}%</span>
                    {selectedMonth === item.month ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                  </div>
                </button>
              ))}
            </div>

            {selectedMonth && selectedMonthData && (
              <div className="mw-detail">
                <div className="mw-detail-header">{selectedMonth} &mdash; Breakdown</div>
                <div className="mw-summary-row">
                  <div className="mw-stat">
                    <span className="mw-stat-label">Collected</span>
                    <span className="mw-stat-val collected">{'\u20B9'}{selectedMonthData.collected.toLocaleString()}</span>
                  </div>
                  <div className="mw-stat">
                    <span className="mw-stat-label">Pending</span>
                    <span className="mw-stat-val pending">{'\u20B9'}{selectedMonthData.pending.toLocaleString()}</span>
                  </div>
                  <div className="mw-stat">
                    <span className="mw-stat-label">Expected</span>
                    <span className="mw-stat-val expected">{'\u20B9'}{selectedMonthData.expected.toLocaleString()}</span>
                  </div>
                </div>
                <div className="mw-class-list">
                  {selectedMonthClassBreakdown.map((c, i) => (
                    <div key={i} className="mw-class-row">
                      <span className="mw-class-name">{c.name}</span>
                      <div className="mw-class-amounts">
                        <span className="mw-cls-collected">{'\u20B9'}{c.collected.toLocaleString()}</span>
                        {c.pending > 0 && (
                          <span className="mw-cls-pending">{'\u20B9'}{c.pending.toLocaleString()} pending</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      <section className="dashboard-section class-breakdown-section">
        <h2>Income by Class</h2>
        {classBreakdown.length > 0 ? (
          <div className="class-breakdown-list">
            {classBreakdown.map(cls => (
              <div key={cls.id} className="class-income-card glass animate-slide-up clickable"
                onClick={() => navigate(`/income/fee-status?classId=${cls.id}`)}>
                <div className="class-info-header">
                  <div>
                    <h3>{cls.name}</h3>
                    <span className="student-badge">{cls.studentCount} Students</span>
                  </div>
                  <span className={`collection-badge ${cls.progress === 100 ? 'fully-paid' : 'pending-collection'}`}>
                    {cls.progress}% Collected
                  </span>
                </div>
                <div className="income-stats-grid">
                  <div className="income-stat-row">
                    <span className="stat-label">Collected:</span>
                    <span className="stat-val collected">{'\u20B9'}{cls.collected}</span>
                  </div>
                  <div className="income-stat-row">
                    <span className="stat-label">Pending:</span>
                    <span className="stat-val pending">{'\u20B9'}{cls.pending}</span>
                  </div>
                  <div className="income-stat-row expected-row">
                    <span className="stat-label">Total Expected:</span>
                    <span className="stat-val expected">{'\u20B9'}{cls.expected}</span>
                  </div>
                </div>
                <div className="progress-bar-track">
                  <div className="progress-bar-fill" style={{ width: `${Math.min(100, cls.progress)}%` }} />
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state glass">
            <p>No classes defined. Please configure classes to view breakdowns.</p>
          </div>
        )}
      </section>
    </div>
  );
};

export default Dashboard;
