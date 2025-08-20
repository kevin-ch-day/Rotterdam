import React from "https://unpkg.com/react@18/umd/react.development.js";
import ReactDOM from "https://unpkg.com/react-dom@18/umd/react-dom.development.js";


function DashboardPage() {
  const [stats, setStats] = React.useState({ devices: 0, jobs: 0, reports: 0 });
  React.useEffect(() => {
    Promise.all([
      api.get("/devices"),
      api.get("/jobs"),
      api.get("/reports"),
    ])
      .then(([d, j, r]) =>
        setStats({ devices: d.length, jobs: j.length, reports: r.length })
      )
      .catch(console.error);
  }, []);
  return React.createElement(
    "div",
    null,
    React.createElement("h3", null, "Dashboard"),
    React.createElement(
      "ul",
      null,
      React.createElement("li", null, `Devices: ${stats.devices}`),
      React.createElement("li", null, `Jobs: ${stats.jobs}`),
      React.createElement("li", null, `Reports: ${stats.reports}`)
    )
  );
}

function DevicesPage() {
  const [devices, setDevices] = React.useState([]);
  React.useEffect(() => {
    api.get("/devices").then(setDevices)
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
    api.get("/devices").then((list) => {
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
    const data = await api.post("/jobs", payload);
    setJobId(data.job_id);
    setReport(null);
    setStatus("pending");
  };

  React.useEffect(() => {
    if (!jobId) return;
    const id = setInterval(async () => {
      const res = await api.get(`/reports/${jobId}`).catch(() => null);
      if (res) {
        setReport(res.report);
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
    api.get("/jobs").then(setJobs)
      .catch(console.error);
  };
  React.useEffect(load, []);
  const remove = async (id) => {
    await api.delete(`/jobs/${id}`);
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

function ReportsPage() {
  const [reports, setReports] = React.useState([]);
  React.useEffect(() => {
    api.get("/reports").then(setReports)
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
            { key: r.job_id },
            React.createElement(
              "td",
              null,
              React.createElement(
                "a",
                { href: `report-detail.html?job_id=${r.job_id}` },
                r.job_id
              )
            ),
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
    api.get("/analytics").then(setAnalytics)
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
    api.get("/analytics/devices").then(setStats)
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

function CurrentDevicePage() {
  const [device, setDevice] = React.useState(null);
  React.useEffect(() => {
    api.get("/devices").then((list) => setDevice(list[0] || null))
      .catch(console.error);
  }, []);
  if (!device) {
    return React.createElement("div", null, "No device connected");
  }
  return React.createElement(
    "div",
    null,
    React.createElement("h3", null, "Current Device"),
    React.createElement(
      "table",
      null,
      React.createElement(
        "tbody",
        null,
        React.createElement(
          "tr",
          null,
          React.createElement("td", null, "Serial"),
          React.createElement("td", null, device.serial)
        ),
        React.createElement(
          "tr",
          null,
          React.createElement("td", null, "Model"),
          React.createElement("td", null, device.model || "-")
        ),
        React.createElement(
          "tr",
          null,
          React.createElement("td", null, "Release"),
          React.createElement("td", null, device.android_release || "-")
        ),
        React.createElement(
          "tr",
          null,
          React.createElement("td", null, "Rooted"),
          React.createElement("td", null, device.is_rooted ? "yes" : "no")
        )
      )
    )
  );
}

function ReportDetailPage({ jobId }) {
  const [id, setId] = React.useState(jobId || "");
  const [detail, setDetail] = React.useState(null);
  const load = async (jid) => {
    if (!jid) return;
    try {
      const reportData = await api.get(`/reports/${jid}`);
      const jobData = await api.get(`/jobs/${jid}`).catch(() => null);
      setDetail({ report: reportData.report, job: jobData });
    } catch (e) {
      setDetail(null);
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
      React.createElement(
        "a",
        { href: "reports.html", style: { marginLeft: "0.5rem" } },
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

const PAGE = window.INITIAL_PAGE || "dashboard";
const DETAIL_ID = window.DETAIL_ID || "";

let appElement;
switch (PAGE) {
  case "dashboard":
    appElement = React.createElement(DashboardPage);
    break;
  case "home":
  case "analyze":
    appElement = React.createElement(AnalyzePage);
    break;
  case "devices":
    appElement = React.createElement(DevicesPage);
    break;
  case "currentDevice":
    appElement = React.createElement(CurrentDevicePage);
    break;
  case "jobs":
    appElement = React.createElement(JobsPage);
    break;
  case "reports":
    appElement = React.createElement(ReportsPage);
    break;
  case "analytics":
    appElement = React.createElement(AnalyticsPage);
    break;
  case "deviceStats":
    appElement = React.createElement(DeviceStatsPage);
    break;
  case "reportDetail":
    appElement = React.createElement(ReportDetailPage, { jobId: DETAIL_ID });
    break;
  default:
    appElement = React.createElement("div", null, "Unknown page");
}

ReactDOM.createRoot(document.getElementById("root")).render(appElement);
