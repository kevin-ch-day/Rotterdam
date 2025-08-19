import React from "https://unpkg.com/react@18/umd/react.development.js";
import ReactDOM from "https://unpkg.com/react-dom@18/umd/react-dom.development.js";

const API_HEADERS = { "X-API-Key": "secret" };

function DevicesPage() {
  const [devices, setDevices] = React.useState([]);
  React.useEffect(() => {
    fetch("/devices", { headers: API_HEADERS })
      .then((r) => r.json())
      .then(setDevices)
      .catch(console.error);
  }, []);
  return React.createElement(
    "div",
    null,
    React.createElement("h3", null, "Devices"),
    React.createElement(
      "table",
      null,
      React.createElement(
        "thead",
        null,
        React.createElement(
          "tr",
          null,
          React.createElement("th", null, "Serial"),
          React.createElement("th", null, "Model"),
          React.createElement("th", null, "Release"),
          React.createElement("th", null, "Rooted")
        )
      ),
      React.createElement(
        "tbody",
        null,
        devices.map((d) =>
          React.createElement(
            "tr",
            { key: d.serial },
            React.createElement("td", null, d.serial),
            React.createElement("td", null, d.model || "-"),
            React.createElement("td", null, d.android_release || "-"),
            React.createElement("td", null, d.is_rooted ? "yes" : "no")
          )
        )
      )
    )
  );
}

function AnalyzePage() {
  const [devices, setDevices] = React.useState([]);
  const [selected, setSelected] = React.useState("");
  const [jobId, setJobId] = React.useState("");
  const [report, setReport] = React.useState(null);
  const [status, setStatus] = React.useState("");

  React.useEffect(() => {
    fetch("/devices", { headers: API_HEADERS })
      .then((r) => r.json())
      .then((list) => {
        setDevices(list);
        if (list.length > 0) setSelected(list[0].serial);
      })
      .catch(console.error);
  }, []);

  const submitJob = async () => {
    const payload = {
      serial: selected,
      static_metrics: { permission_density: Math.random() },
      dynamic_metrics: { permission_invocation_count: Math.floor(Math.random() * 20) },
    };
    const res = await fetch("/jobs", {
      method: "POST",
      headers: { "Content-Type": "application/json", ...API_HEADERS },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    setJobId(data.job_id);
    setReport(null);
    setStatus("pending");
  };

  React.useEffect(() => {
    if (!jobId) return;
    const id = setInterval(async () => {
      const res = await fetch(`/reports/${jobId}`, { headers: API_HEADERS });
      if (res.status === 200) {
        const data = await res.json();
        setReport(data.report);
        setStatus("completed");
        clearInterval(id);
      }
    }, 1000);
    return () => clearInterval(id);
  }, [jobId]);

  return React.createElement(
    "div",
    null,
    React.createElement(
      "div",
      null,
      React.createElement(
        "select",
        {
          value: selected,
          onChange: (e) => setSelected(e.target.value),
        },
        devices.map((d) =>
          React.createElement("option", { key: d.serial, value: d.serial }, d.serial)
        )
      ),
      React.createElement(
        "button",
        { onClick: submitJob, disabled: !selected },
        "Analyze"
      ),
      jobId && React.createElement("span", null, ` Job: ${status || "pending"}`)
    ),
    report
      ? React.createElement(
          "div",
          null,
          React.createElement("h3", null, `Risk Score: ${report.risk.score}`),
          React.createElement("p", null, report.risk.rationale),
          React.createElement(
            "table",
            null,
            React.createElement(
              "tbody",
              null,
              Object.entries(report.risk.breakdown).map(([k, v]) =>
                React.createElement(
                  "tr",
                  { key: k },
                  React.createElement("td", null, k),
                  React.createElement("td", null, v)
                )
              )
            )
          )
        )
      : React.createElement("pre", null, JSON.stringify(devices, null, 2))
  );
}

function JobsPage() {
  const [jobs, setJobs] = React.useState([]);
  const load = () => {
    fetch("/jobs", { headers: API_HEADERS })
      .then((r) => r.json())
      .then(setJobs)
      .catch(console.error);
  };
  React.useEffect(load, []);
  const remove = async (id) => {
    await fetch(`/jobs/${id}`, { method: "DELETE", headers: API_HEADERS });
    load();
  };
  return React.createElement(
    "div",
    null,
    React.createElement("h3", null, "Jobs"),
    React.createElement(
      "table",
      null,
      React.createElement(
        "thead",
        null,
        React.createElement(
          "tr",
          null,
          React.createElement("th", null, "Job ID"),
          React.createElement("th", null, "Status"),
          React.createElement("th", null, "Actions")
        )
      ),
      React.createElement(
        "tbody",
        null,
        jobs.map((j) =>
          React.createElement(
            "tr",
            { key: j.job_id },
            React.createElement("td", null, j.job_id),
            React.createElement("td", null, j.status),
            React.createElement(
              "td",
              null,
              React.createElement(
                "button",
                { onClick: () => remove(j.job_id) },
                "Delete"
              )
            )
          )
        )
      )
    )
  );
}

function ReportsPage({ onSelect }) {
  const [reports, setReports] = React.useState([]);
  React.useEffect(() => {
    fetch("/reports", { headers: API_HEADERS })
      .then((r) => r.json())
      .then(setReports)
      .catch(console.error);
  }, []);
  return React.createElement(
    "div",
    null,
    React.createElement("h3", null, "Reports"),
    React.createElement(
      "table",
      null,
      React.createElement(
        "thead",
        null,
        React.createElement(
          "tr",
          null,
          React.createElement("th", null, "Job ID"),
          React.createElement("th", null, "Score")
        )
      ),
      React.createElement(
        "tbody",
        null,
        reports.map((r) =>
          React.createElement(
            "tr",
            {
              key: r.job_id,
              onClick: () => onSelect && onSelect(r.job_id),
              style: { cursor: "pointer" },
            },
            React.createElement("td", null, r.job_id),
            React.createElement("td", null, r.risk.score)
          )
        )
      )
    )
  );
}

function AnalyticsPage() {
  const [analytics, setAnalytics] = React.useState(null);
  React.useEffect(() => {
    fetch("/analytics", { headers: API_HEADERS })
      .then((r) => r.json())
      .then(setAnalytics)
      .catch(console.error);
  }, []);
  return React.createElement(
    "div",
    null,
    React.createElement("h3", null, "Analytics"),
    analytics &&
      React.createElement(
        "ul",
        null,
        React.createElement("li", null, `Reports: ${analytics.reports}`),
        React.createElement(
          "li",
          null,
          `Average Score: ${analytics.average_score ?? "n/a"}`
        ),
        React.createElement(
          "li",
          null,
          `Min Score: ${analytics.min_score ?? "n/a"}`
        ),
        React.createElement(
          "li",
          null,
          `Max Score: ${analytics.max_score ?? "n/a"}`
        )
      )
  );
}

function DeviceStatsPage() {
  const [stats, setStats] = React.useState([]);
  React.useEffect(() => {
    fetch("/analytics/devices", { headers: API_HEADERS })
      .then((r) => r.json())
      .then(setStats)
      .catch(console.error);
  }, []);
  return React.createElement(
    "div",
    null,
    React.createElement("h3", null, "Device Stats"),
    React.createElement(
      "table",
      null,
      React.createElement(
        "thead",
        null,
        React.createElement(
          "tr",
          null,
          React.createElement("th", null, "Serial"),
          React.createElement("th", null, "Reports"),
          React.createElement("th", null, "Average"),
          React.createElement("th", null, "Min"),
          React.createElement("th", null, "Max")
        )
      ),
      React.createElement(
        "tbody",
        null,
        stats.map((s) =>
          React.createElement(
            "tr",
            { key: s.serial },
            React.createElement("td", null, s.serial),
            React.createElement("td", null, s.reports),
            React.createElement("td", null, s.average_score),
            React.createElement("td", null, s.min_score),
            React.createElement("td", null, s.max_score)
          )
        )
      )
    )
  );
}

function ReportDetailPage({ jobId, onBack }) {
  const [id, setId] = React.useState(jobId || "");
  const [detail, setDetail] = React.useState(null);
  const load = async (jid) => {
    if (!jid) return;
    try {
      const reportRes = await fetch(`/reports/${jid}`, { headers: API_HEADERS });
      if (reportRes.status !== 200) {
        setDetail(null);
        return;
      }
      const reportData = await reportRes.json();
      const jobRes = await fetch(`/jobs/${jid}`, { headers: API_HEADERS });
      const jobData = jobRes.status === 200 ? await jobRes.json() : null;
      setDetail({ report: reportData.report, job: jobData });
    } catch (e) {
      console.error(e);
    }
  };
  React.useEffect(() => {
    if (jobId) load(jobId);
  }, [jobId]);
  return React.createElement(
    "div",
    null,
    React.createElement("h3", null, "Report Detail"),
    React.createElement(
      "div",
      null,
      React.createElement("input", {
        value: id,
        onChange: (e) => setId(e.target.value),
        placeholder: "Job ID",
      }),
      React.createElement(
        "button",
        { onClick: () => load(id), disabled: !id },
        "Load"
      ),
      onBack &&
        React.createElement(
          "button",
          { onClick: onBack, style: { marginLeft: "0.5rem" } },
          "Back"
        )
    ),
    detail &&
      detail.report &&
      React.createElement(
        "div",
        null,
        React.createElement(
          "h4",
          null,
          `Risk Score: ${detail.report.risk.score}`
        ),
        React.createElement("p", null, detail.report.risk.rationale),
        React.createElement(
          "table",
          null,
          React.createElement(
            "tbody",
            null,
            Object.entries(detail.report.risk.breakdown).map(([k, v]) =>
              React.createElement(
                "tr",
                { key: k },
                React.createElement("td", null, k),
                React.createElement("td", null, v)
              )
            )
          )
        ),
        detail.job &&
          detail.job.request &&
          React.createElement(
            "pre",
            null,
            JSON.stringify(detail.job.request, null, 2)
          )
      )
  );
}

function App() {
  const [page, setPage] = React.useState("home");
  const [detailId, setDetailId] = React.useState("");
  return React.createElement(
    "div",
    null,
    React.createElement("h1", null, "Rotterdam UI"),
    React.createElement(
      "nav",
      null,
      React.createElement(
        "button",
        { onClick: () => setPage("home") },
        "Analyze"
      ),
      React.createElement(
        "button",
        { onClick: () => setPage("devices") },
        "Devices"
      ),
      React.createElement(
        "button",
        { onClick: () => setPage("jobs") },
        "Jobs"
      ),
      React.createElement(
        "button",
        { onClick: () => setPage("reports") },
        "Reports"
      ),
      React.createElement(
        "button",
        { onClick: () => setPage("analytics") },
        "Analytics"
      ),
      React.createElement(
        "button",
        { onClick: () => setPage("deviceStats") },
        "Device Stats"
      )
    ),
    page === "home" && React.createElement(AnalyzePage),
    page === "devices" && React.createElement(DevicesPage),
    page === "jobs" && React.createElement(JobsPage),
    page === "reports" &&
      React.createElement(ReportsPage, {
        onSelect: (jid) => {
          setDetailId(jid);
          setPage("reportDetail");
        },
      }),
    page === "analytics" && React.createElement(AnalyticsPage),
    page === "deviceStats" && React.createElement(DeviceStatsPage),
    page === "reportDetail" &&
      React.createElement(ReportDetailPage, {
        jobId: detailId,
        onBack: () => setPage("reports"),
      })
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(
  React.createElement(App)
);
