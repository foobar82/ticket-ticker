// Ticket detail interactions: status change, self-assign, comments (§7.2/§9).
(function () {
  "use strict";

  var article = document.querySelector(".ticket-detail");
  if (!article) return;
  var ticketId = article.dataset.ticketId;

  function esc(s) {
    var d = document.createElement("div");
    d.textContent = s == null ? "" : s;
    return d.innerHTML;
  }

  function flash(el, msg, ok) {
    if (!el) return;
    el.textContent = msg;
    el.className = "feedback " + (ok ? "ok" : "err");
    if (ok) {
      setTimeout(function () { el.textContent = ""; el.className = "feedback"; }, 2500);
    }
  }

  function patch(payload) {
    return fetch("/api/tickets/" + ticketId, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(function (r) {
      return r.json().then(function (data) {
        if (!r.ok) throw new Error(data.error || "Request failed");
        return data.ticket;
      });
    });
  }

  // --- Status change ---
  var statusSelect = document.getElementById("status-select");
  var statusFeedback = document.getElementById("status-feedback");
  if (statusSelect) {
    statusSelect.addEventListener("change", function () {
      patch({ status: statusSelect.value })
        .then(function () { flash(statusFeedback, "Saved ✓", true); })
        .catch(function (e) { flash(statusFeedback, e.message, false); });
    });
  }

  // --- Assign / unassign (self-assign only, §7.2) ---
  var assignBtn = document.getElementById("assign-btn");
  var unassignBtn = document.getElementById("unassign-btn");
  var assigneeLabel = document.getElementById("assignee-label");

  function reflectAssignee(name) {
    assigneeLabel.textContent = name || "Unassigned";
    if (unassignBtn) unassignBtn.hidden = !name;
    var me = window.getCurrentUser();
    if (assignBtn) {
      assignBtn.textContent = name === me ? "Assigned to you" : "Assign to me";
      assignBtn.disabled = !!name && name === me;
    }
  }

  if (assignBtn) {
    assignBtn.addEventListener("click", function () {
      var me = window.getCurrentUser();
      if (!me) {
        alert("Pick your name (top right) first.");
        return;
      }
      patch({ assignee: me })
        .then(function (t) { reflectAssignee(t.assignee); })
        .catch(function (e) { alert(e.message); });
    });
  }
  if (unassignBtn) {
    unassignBtn.addEventListener("click", function () {
      patch({ assignee: "" })
        .then(function (t) { reflectAssignee(t.assignee); })
        .catch(function (e) { alert(e.message); });
    });
  }
  // Initialise button label against the current user.
  reflectAssignee(assigneeLabel.textContent.trim() === "Unassigned"
    ? "" : assigneeLabel.textContent.trim());
  document.addEventListener("currentuserchange", function () {
    reflectAssignee(unassignBtn && !unassignBtn.hidden
      ? assigneeLabel.textContent.trim() : "");
  });

  // --- Comments ---
  var form = document.getElementById("comment-form");
  var bodyInput = document.getElementById("comment-body");
  var commentFeedback = document.getElementById("comment-feedback");
  var list = document.getElementById("comment-list");

  if (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var me = window.getCurrentUser();
      if (!me) {
        flash(commentFeedback, "Pick your name first.", false);
        return;
      }
      var body = bodyInput.value.trim();
      if (!body) return;

      fetch("/api/tickets/" + ticketId + "/comments", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ author: me, body: body }),
      })
        .then(function (r) {
          return r.json().then(function (data) {
            if (!r.ok) throw new Error(data.error || "Failed");
            return data.comment;
          });
        })
        .then(function (c) {
          var none = document.getElementById("no-comments");
          if (none) none.remove();
          var li = document.createElement("li");
          li.innerHTML =
            '<span class="comment-author">' + esc(c.author) + "</span> " +
            '<span class="comment-time">' +
            new Date(c.created_at).toLocaleString() + "</span>" +
            '<div class="comment-body">' + esc(c.body) + "</div>";
          list.appendChild(li);
          bodyInput.value = "";
          flash(commentFeedback, "Added ✓", true);
        })
        .catch(function (e2) { flash(commentFeedback, e2.message, false); });
    });
  }
})();
