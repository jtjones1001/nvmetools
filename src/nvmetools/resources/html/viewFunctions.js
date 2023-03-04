/* -------------------------------------------------------------------------------------------------
/ Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
/-------------------------------------------------------------------------------------------------
/ Functions to unhide sections and parameter views
/
/ Version 3.5.23 - Joe Jones
/ ------------------------------------------------------------------------------------------------- */

/* Unhide a section */

function gotoSection(newSection, update_icon = true) {
  console.log("Going to section: " + newSection);

  const sections = document.getElementsByTagName("section");
  for (let i = 0; i < sections.length; i++) {
    sections[i].classList.add("hide");
  }
  globalSelectedSection = document.getElementById(`${newSection}-section`);
  globalSelectedSection.classList.remove("hide");

  if (update_icon == false) {
    return;
  }

  const icons = document.getElementsByClassName("sb-icon");
  for (let i = 0; i < icons.length; i++) {
    icons[i].classList.remove("active");
  }
  document.getElementById(`sb-${newSection}`).classList.add("active");
}

/* Runs when a new requirement selected from rqmt list tables */

function selectRequirement(newRequirement) {
  console.log("Selecting requirement : " + newRequirement);

  globalSelectedRequirement = newRequirement;
  updateRequirementListTable("rqmt-list", sortedRqmtList);
  updateRequirementListTable("rqmt-view-list", sortedRqmtList);
  updateVerificationListTable(selectedVerificationListData);
  gotoSection("rqmt");
}

/* Runs when a new test selected from the test list table */

function selectTest(newSelectedTest) {
  console.log("Selecting requirement : " + newSelectedTest);

  globalSelectedTest = newSelectedTest;
  var testViewListBody = document
    .getElementById("test-view-list")
    .getElementsByTagName("tbody")[0];

  for (let i = 0; i < testViewListBody.rows.length; i++) {
    testViewListBody.rows[i].classList.remove("active");
    if (testViewListBody.rows[i].cells[0].innerHTML == globalSelectedTest) {
      testViewListBody.rows[i].classList.add("active");
    }
  }
  testDetails = document.getElementsByClassName("test-info");
  for (let i = 0; i < testDetails.length; i++) {
    testDetails[i].classList.add("hide");
  }

  let activeDetail = document.getElementById(`test${globalSelectedTest}`);
  activeDetail.classList.remove("hide");
  gotoSection("test");
}

/* These hide or show the test details table */

function collapseTests() {
  detail_tables = document.getElementsByClassName("test_detail");
  for (let i = 0; i < detail_tables.length; i++) {
    detail_tables[i].className = "test_detail hide";
  }
  document.getElementById("expanded").classList.add("hide");
  document.getElementById("collapsed").classList.remove("hide");
}
function expandTests() {
  detail_tables = document.getElementsByClassName("test_detail");
  for (let i = 0; i < detail_tables.length; i++) {
    detail_tables[i].className = "test_detail";
  }
  document.getElementById("collapsed").classList.add("hide");
  document.getElementById("expanded").classList.remove("hide");
}

/* Sets the parameter view on the parameter section */

function setParameterView(parameter) {
  console.log("Setting parameter view " + parameter);

  gotoSection("parameter");
  buttons = document.getElementsByClassName("param-select");
  for (var i = 0; i < buttons.length; i++) {
    buttons[i].classList.remove("active");
  }
  document.getElementById(`pv-dropdown`).classList.remove("active");

  if (parameter == "dropdown") {
    document.getElementById(`pv-dropdown`).classList.add("active");
    parameter = document.getElementById("pv-dropdown").innerText;
  } else if (parameterDefaultOptions.includes(parameter)) {
    document.getElementById(`pv-${parameter}`).classList.add("active");
  } else {
    document.getElementById(`pv-dropdown`).classList.add("active");
    document.getElementById("pv-dropdown").innerHTML =
      `<span style= "margin-left: auto">${parameter.toUpperCase()}</span>` +
      caretDown;
  }

  globalParameterView = parameter.toLowerCase();

  document.getElementById("event-entries").classList.add("hide");
  document.getElementById("error-entries").classList.add("hide");
  document.getElementById("command-entries").classList.add("hide");
  document.getElementById("diagnostic-entries").classList.add("hide");

  document.getElementById("logrow").classList.add("hide");

  if (globalParameterView == "errors") {
    document.getElementById("error-entries").classList.remove("hide");
    document.getElementById("logrow").classList.remove("hide");
    document.getElementById((id = "log entries name")).innerHTML =
      "ERROR LOG ENTRIES";
  } else if (globalParameterView == "events") {
    document.getElementById("event-entries").classList.remove("hide");
    document.getElementById("logrow").classList.remove("hide");
    document.getElementById((id = "log entries name")).innerHTML =
      "EVENT LOG ENTRIES";
  } else if (globalParameterView == "commands") {
    document.getElementById("command-entries").classList.remove("hide");
    document.getElementById("logrow").classList.remove("hide");
    document.getElementById((id = "log entries name")).innerHTML =
      "COMMAND LOG ENTRIES";
  } else if (globalParameterView == "self-tests") {
    document.getElementById("diagnostic-entries").classList.remove("hide");
    document.getElementById("logrow").classList.remove("hide");
    document.getElementById((id = "log entries name")).innerHTML =
      "SELF-TEST LOG ENTRIES";
  }
  updateData();
}
