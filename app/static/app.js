// Name picker (spec §4 / §7.3). The "current user" lives in localStorage and
// is purely a convenience for "assigned to me" filtering -- NOT auth.
(function () {
  "use strict";
  var KEY = "ticketing.currentUser";

  window.getCurrentUser = function () {
    return localStorage.getItem(KEY) || "";
  };

  window.setCurrentUser = function (name) {
    if (name) {
      localStorage.setItem(KEY, name);
    } else {
      localStorage.removeItem(KEY);
    }
    document.dispatchEvent(
      new CustomEvent("currentuserchange", { detail: { user: name } })
    );
  };

  document.addEventListener("DOMContentLoaded", function () {
    var select = document.getElementById("user-select");
    if (!select) return;
    var current = window.getCurrentUser();
    if (current) {
      // Add the stored name even if it's no longer in the roster, so the
      // picker reflects reality.
      if (!Array.prototype.some.call(select.options, function (o) {
            return o.value === current;
          })) {
        var opt = document.createElement("option");
        opt.value = current;
        opt.textContent = current + " (not in roster)";
        select.appendChild(opt);
      }
      select.value = current;
    }
    select.addEventListener("change", function () {
      window.setCurrentUser(select.value);
    });
  });
})();
