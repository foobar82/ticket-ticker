// Loads ticket rows for the current view from the JSON API (spec §7.1/§9).
(function () {
  "use strict";

  var STATUS_CLASS = {
    "To Do": "status-todo",
    "In Progress": "status-progress",
    "Closed": "status-closed",
  };

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  function fmtTime(iso) {
    if (!iso) return "";
    var d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleString();
  }

  function render(tickets) {
    var body = document.getElementById("tickets-body");
    if (!tickets.length) {
      body.innerHTML =
        '<tr><td colspan="5" class="muted">No tickets.</td></tr>';
      return;
    }
    body.innerHTML = tickets
      .map(function (t) {
        var cls = STATUS_CLASS[t.status] || "";
        return (
          '<tr onclick="window.location=\'/tickets/' +
          t.id +
          "'\">" +
          '<td class="col-id">' + t.id + "</td>" +
          "<td>" + esc(t.title) + "</td>" +
          '<td class="col-status"><span class="badge ' + cls + '">' +
          esc(t.status) + "</span></td>" +
          '<td class="col-assignee">' +
          (t.assignee ? esc(t.assignee) : '<span class="muted">—</span>') +
          "</td>" +
          '<td class="col-updated">' + fmtTime(t.updated_at) + "</td>" +
          "</tr>"
        );
      })
      .join("");
  }

  function load() {
    var view = window.TICKET_VIEW || "all";
    var user = window.getCurrentUser();
    var hint = document.getElementById("list-hint");
    var body = document.getElementById("tickets-body");

    if ((view === "mine" || view === "mine_open") && !user) {
      if (hint) hint.hidden = false;
      body.innerHTML =
        '<tr><td colspan="5" class="muted">Pick your name to load.</td></tr>';
      return;
    }
    if (hint) hint.hidden = true;

    var url = "/api/tickets?view=" + encodeURIComponent(view);
    if (user) url += "&user=" + encodeURIComponent(user);

    fetch(url)
      .then(function (r) { return r.json(); })
      .then(function (data) { render(data.tickets || []); })
      .catch(function () {
        body.innerHTML =
          '<tr><td colspan="5" class="muted">Failed to load tickets.</td></tr>';
      });
  }

  document.addEventListener("DOMContentLoaded", load);
  document.addEventListener("currentuserchange", load);
})();
