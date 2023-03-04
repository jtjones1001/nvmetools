/* -------------------------------------------------------------------------------------------------
/ Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
/-------------------------------------------------------------------------------------------------
/ Functions to update tables and health info
/
/ Version 3.5.23 - Joe Jones
/ ------------------------------------------------------------------------------------------------- */
var bannerHealth = "na";
const maxTempSensor = 8;

const failBadge = `<td class="status-col"><span class="table-badge fail">FAIL</span></td>`;
const passBadge = `<td class="status-col"><span class="table-badge pass">PASS</span></td>`;
const skipBadge = `<td class="status-col"><span class="table-badge">SKIP</span></td>`;

const noHealth =
  '<svg  style="position: relative; top: 0px; right: 0px; " xmlns="http://www.w3.org/2000/svg" width="8" height="8" fill="transparent" class="bi bi-circle-fill" viewBox="0 0 16 16"><circle cx="8" cy="8" r="8"/></svg>';
const suspectHealth =
  '<svg style="position: relative; top: 0px; right: 0px; " xmlns="http://www.w3.org/2000/svg" width="8" height="8" fill="var(--dark-yellow)" class="bi bi-circle-fill" viewBox="0 0 16 16"><circle cx="8" cy="8" r="8"/></svg>';
const criticalHealth =
  '<svg style="position: relative; top: 0px; right: 0px; " xmlns="http://www.w3.org/2000/svg" width="8" height="8" fill="var(--dark-red)" class="bi bi-circle-fill" viewBox="0 0 16 16"><circle cx="8" cy="8" r="8"/></svg>';
const missingHealth =
  '<svg style="position: relative; top: 0px; right: 0px; " xmlns="http://www.w3.org/2000/svg" width="8" height="8" fill="grey" class="bi bi-circle-fill" viewBox="0 0 16 16"><circle cx="8" cy="8" r="8"/></svg>';

const criticalText =
  "The NVMe drive is operating, or has extensively operated, outside the normal range indicating an elevated risk of failure, damage or severely degraded performance. Action should be taken to resolve the issue.";
const suspectText =
  "The NVMe drive may be operating, or has extensively operated, outside the normal range.  Review the data to determine if action should be taken to resolve the issue.";
const goodText = "The NVMe drive is operating normally.";
const healthItemLookup = {
  "dt-total-value": "Current Number Of Self-Tests",
  "dt-fails-value": "Number Of Failed Self-Tests",
  "dt-last-value": "Last Self-test",

  "usage-used-value": "Percentage Used",
  "usage-spare-value": "Available Spare",
  "usage-poh-value": "Power On Hours",
  "usage-data-value": "Data Written TB",
  "usage-writes-value": "Drive Writes",

  "smart-tile-reliability-value": "NVM Subsystem Unreliable",
  "smart-tile-pmr-value": "Persistent Memory Unreliable",
  "smart-tile-readonly-value": "Media in Read-only",
  "smart-tile-volatile-value": "Volatile Memory Backup Failed",
  "smart-tile-integrity-value": "Media and Data Integrity Errors",

  "pcibw-value": "PCI Bandwidth",
  "pcibw-rated": "PCI Rated Bandwidth",
  "pcispeed-value": "PCI Speed",
  "pcispeed-rated": "PCI Rated Speed",
  "pciwidth-value": "PCI Width",
  "pciwidth-rated": "PCI Rated Width",

  "pe-tile-smart-value": "SMART Errors",
  "pe-tile-pci-value": "PCIe Errors",
  "pe-tile-data-value": "Data Errors",
  "pe-tile-fatal-value": "Controller Fatal Events",

  "ctemp-value": "Composite Temperature",
  "tsensor1-value": "Temperature Sensor 1",
  "tsensor2-value": "Temperature Sensor 2",
  "tsensor3-value": "Temperature Sensor 3",
  "tsensor4-value": "Temperature Sensor 4",
  "tsensor5-value": "Temperature Sensor 5",
  "tsensor6-value": "Temperature Sensor 6",
  "tsensor7-value": "Temperature Sensor 7",
  "tsensor8-value": "Temperature Sensor 8",

  "pe-tile-pci-value": "PCIe Errors",
  "pe-tile-fatal-value": "Controller Fatal Events",

  "thr-total-value": "Minutes Throttled",
  "thr-total-percent": "Percent Throttled",

  "cctemp-time": "Critical Composite Temperature Time",
  "wctemp-time": "Warning Composite Temperature Time",
  "tmt2-time": "Thermal Management Temperature 2 Time",
  "tmt1-time": "Thermal Management Temperature 1 Time",

  "wctemp-value": "Warning Composite Temperature Threshold (WCTEMP)",
  "cctemp-value": "Critical Composite Temperature Threshold (CCTEMP)",

  "tmt1-value": "Thermal Management Temperature 1 (TMT1)",
  "tmt2-value": "Thermal Management Temperature 2 (TMT2)",
};

var allParametersList = {};
var parameterArray = [];

var diagnosticLogArray = allData[activeNvme]["self-test log"];
var commandLogArray = allData[activeNvme]["command log"];
var errorLogArray = allData[activeNvme]["error log"];
var eventLogArray = allData[activeNvme]["event log"];
var systemData = allData[activeNvme]["system"];
var healthDictionary = allData[activeNvme]["health"];
var parameterDictionary = allData[activeNvme]["parameters"];

function updateChart(element_by_id, labels, values) {
  let main_body = document.getElementById("mainbody");
  const tmpChart = new Chart(element_by_id, {
    type: "doughnut",
    data: {
      labels: labels,
      datasets: [
        {
          data: values,
          backgroundColor: [
            getComputedStyle(main_body).getPropertyValue("--dark-green"),
            getComputedStyle(main_body).getPropertyValue("--dark-red"),
            getComputedStyle(main_body).getPropertyValue("--dark-grey"),
          ],
          hoverOffset: 4,
        },
      ],
    },
    options: {
      responsive: false,
      plugins: {
        legend: {
          display: true,
          position: "right",
          labels: { boxWidth: 12, font: { size: 11 }, color: "##161616" },
        },
        tooltip: {
          callbacks: {
            label: function (context, data) {
              let label = context.label;
              let value = context.formattedValue;
              let sum = 0;
              let dataArr = context.chart.data.datasets[0].data;
              dataArr.map((data) => {
                sum += Number(data);
              });
              return (
                label +
                ": " +
                value +
                " (" +
                ((value * 100) / sum).toFixed(1) +
                "%)"
              );
            },
          },
        },
      },
    },
  });
}

function updateHealthState(current, proposed) {
  if (proposed.toLowerCase() == "critical") {
    return "Critical";
  } else if (proposed.toLowerCase() == "suspect") {
    if (current.toLowerCase() != "critical") {
      return "Suspect";
    }
  } else if (proposed.toLowerCase() == "missing") {
    if (
      current.toLowerCase() != "critical" &&
      current.toLowerCase() != "suspect"
    ) {
      return "Missing";
    }
  }
  return current;
}

function updateHealthSection() {
  bannerHealth = "Good";
  var healthGroup = {
    "DIAGNOSTIC SELF-TEST": { state: "Good", id: "diag-tile" },
    USAGE: { state: "Good", id: "usage-tile" },
    TEMPERATURE: { state: "Good", id: "temp-tile" },
    "TIME THROTTLED": { state: "Good", id: "throttle-tile" },
    "PERSISTENT EVENTS": { state: "Good", id: "events-tile" },
    "PCI EXPRESS BANDWIDTH": { state: "Good", id: "pcibw-tile" },
    "SMART ERRORS": { state: "Good", id: "smart-tile" },
    "OS ERRORS": { state: "Good", id: "os-tile" },
    CAPACITY: { state: "Good", id: "capacity-tile" },
  };

  for (const [id, value] of Object.entries(healthItemLookup)) {
    if (value in allParametersList) {
      document.getElementById(id).innerHTML = allParametersList[value];
    }
  }

  for (const [name, value] of Object.entries(healthDictionary)) {
    bannerHealth = updateHealthState(bannerHealth, value["state"]);
    healthGroup[value["group"]]["state"] = updateHealthState(
      healthGroup[value["group"]]["state"],
      value["state"]
    );

    let healthState = value["state"].toLowerCase();
    if (healthState == "good") {
      icon = noHealth;
    } else if (healthState == "suspect") {
      icon = suspectHealth;
    } else if (healthState == "missing") {
      icon = missingHealth;
    } else {
      icon = criticalHealth;
    }
    document.getElementById(name).innerHTML = icon;
  }
  for (const [name, value] of Object.entries(healthGroup)) {
    let healthState = value["state"].toLowerCase();

    console.log( "Setting health tile " + name + value["id"] + " " + healthState);

    if (healthState == "good") {
      document.getElementById(value["id"]).style = "background-color: var(--lighter-grey) !important";
      document.getElementById(value["id"]).parentNode.style ="border-color: var(--border-color) !important;";
    } else if (healthState == "missing") {
      document.getElementById(value["id"]).style ="background-color: var(--lighter-grey) !important";
      document.getElementById(value["id"]).parentNode.style ="border-color: var(--border-color) !important;";
    } else if (healthState == "suspect") {
      document.getElementById(value["id"]).style = "border-color: var(--dark-yellow); background-color: var(--dark-yellow) !important";
      document.getElementById(value["id"]).parentNode.style ="border-color: var(--dark-yellow) !important;";
    } else {
      document.getElementById(value["id"]).style ="border-color: var(--dark-red) !important;background-color: var(--dark-red) !important; color:white;";
      document.getElementById(value["id"]).parentNode.style ="border-color: var(--dark-red2) !important;";
    }
    document.getElementById(value["id"]).innerHTML = name;
  }
  elementId = document.getElementById("nvme-health");
  if (bannerHealth == "Critical") {
    elementId.innerHTML = `<b>HEALTH<br>CRITICAL</b>`;
    elementId.className = "hdr-badge critical";

    document.getElementById("health-banner").innerHTML = "HEALTH IS CRITICAL";
    document.getElementById("health-banner-text").innerHTML = criticalText;
    document.getElementById("health-banner").style ="border-color: var(--dark-red);background-color: var(--dark-red); color:white;";
    document.getElementById("health-banner").parentNode.style ="border-color: var(--dark-red2);";

  } else if (bannerHealth == "Suspect") {
    elementId.innerHTML = `<b>HEALTH<br>SUSPECT</b>`;
    elementId.className = "hdr-badge suspect";

    document.getElementById("health-banner").innerHTML = "HEALTH IS SUSPECT";
    document.getElementById("health-banner-text").innerHTML = suspectText;
    document.getElementById("health-banner").style ="border-color: var(--dark-yellow);background-color: var(--dark-yellow) !important";
    document.getElementById("health-banner").parentNode.style ="border-color: var(--dark-yellow2);";
  } else if (bannerHealth == "Good" || bannerHealth == "Missing") {
    elementId.innerHTML = `<b>HEALTH<br>GOOD</b>`;
    elementId.className = "hdr-badge good";

    document.getElementById("health-banner").innerHTML = "HEALTH IS GOOD";
    document.getElementById("health-banner-text").innerHTML = goodText;
    document.getElementById("health-banner").style = "border-color: var(--dark-green);background-color: var(--dark-green) !important; color:white;";
    document.getElementById("health-banner").parentNode.style ="border-color: var(--dark-green2);";

  }

  if (
    allParametersList["Thermal Management Temperature 1 (TMT1)"] == "Disabled"
  ) {
    document.getElementById("tmt1-row").className = "hide";
  } else {
    document.getElementById("tmt2-row").className = "";
  }
  if (
    allParametersList["Thermal Management Temperature 2 (TMT2)"] == "Disabled"
  ) {
    document.getElementById("tmt2-row").className = "hide";
  } else {
    document.getElementById("tmt1-row").className = "";
  }

  if ("Persistent Memory Unreliable" in allParametersList) {
    document.getElementById("pmr-row").className = "";
  } else {
    document.getElementById("pmr-row").className = "hide";
  }

  if (allParametersList["Persistent Event Log"] == "Supported") {
    document.getElementById("persistent-event-table").className = "tile-table";
    document.getElementById("pel-support-msg").className = "hide";
  } else {
    document.getElementById("persistent-event-table").className =
      "tile-table hide";
    document.getElementById("pel-support-msg").className = "";
  }

  for (let i = 1; i <= maxTempSensor; i++) {
    if (`Temperature Sensor ${i}` in allParametersList) {
      document.getElementById(`tr-tsensor${i}`).className = "";
    } else {
      document.getElementById(`tr-tsensor${i}`).className = "hide";
    }
  }
  var dataWrittenGb = allParametersList["Data Written"].split(" ")[0];
  var dataWrittenTb = parseInt(dataWrittenGb.replace(",", "")) / 1000.0;
  var dataReadGb = allParametersList["Data Read"].split(" ")[0];
  var dataReadTb = parseInt(dataReadGb.replace(",", "")) / 1000.0;

  document.getElementById(
    "nvme-fw"
  ).innerHTML = `<b>FIRMWARE</b><br>${allParametersList["Firmware Revision (FR)"]}`;
  document.getElementById(
    "nvme-written"
  ).innerHTML = `<b>DATA WRITTEN</b><br>${dataWrittenTb.toFixed(1)} TB`;
  document.getElementById(
    "nvme-read"
  ).innerHTML = `<b>DATA READ</b><br>${dataReadTb.toFixed(1)} TB`;
  document.getElementById(
    "nvme-wear"
  ).innerHTML = `<b>USAGE</b><br>${allParametersList["Percentage Used"]}`;
  document.getElementById(
    "nvme-temp"
  ).innerHTML = `<b>TEMPERATURE</b><br>${allParametersList["Composite Temperature"]}`;
  document.getElementById(
    "nvme-throttle"
  ).innerHTML = `<b>THROTTLE</b><br>${allParametersList["Percent Throttled"]}`;
}

function passValue(value) {
  return `<td>${value}</td>`;
}
function failValue(value) {
  return `<td style="color:red;font-weight:bold;">${value}</td>`;
}

function sortTableData(dataset, tableData) {
  console.log("sortTableData called with " + tableData.length + " rows");
  let column = dataset.column;
  let order = dataset.order;
  if (order === "desc") {
    dataset.order = "asc";
    tableData = tableData.sort((a, b) =>
      String(a[column]).localeCompare(b[column], undefined, {
        numeric: true,
        sensitivity: "base",
      })
    );
  } else {
    dataset.order = "desc";
    tableData = tableData.sort((a, b) =>
      String(b[column]).localeCompare(a[column], undefined, {
        numeric: true,
        sensitivity: "base",
      })
    );
  }
  return tableData;
}

document
  .querySelectorAll(".parameter-table th, .active-parameter-table th")
  .forEach(function (header, index) {
    header.addEventListener("click", function () {
      const tableId = this.parentNode.parentNode.parentNode.id;
      console.log(`Sort list on ${tableId} col: ${this.dataset.column}`);

      if (tableId == "command-entries") {
        commandLogArray = sortTableData(this.dataset, commandLogArray);
        updateCommandLogTable();
      } else if (tableId == "error-entries") {
        errorLogArray = sortTableData(this.dataset, errorLogArray);
        updateErrorLogTable();
      } else if (tableId == "event-entries") {
        eventLogArray = sortTableData(this.dataset, eventLogArray);
        updateEventLogTable();
      } else if (tableId == "diagnostic-entries") {
        diagnosticLogArray = sortTableData(this.dataset, diagnosticLogArray);
        updateDiagnosticLogTable();
      } else if (tableId == "test-list" || tableId == "test-view-list") {
        sortedTestList = sortTableData(this.dataset, sortedTestList);
        updateTestListTable(tableId, sortedTestList);
      } else if (tableId == "rqmt-list" || tableId == "rqmt-view-list") {
        sortedRqmtList = sortTableData(this.dataset, sortedRqmtList);
        updateRequirementListTable(tableId, sortedRqmtList);
      } else if (tableId == "rqmt-verifications") {
        selectedVerificationListData = sortTableData(
          this.dataset,
          selectedVerificationListData
        );
        updateVerificationListTable(selectedVerificationListData);
      } else {
        parameterArray = sortTableData(this.dataset, parameterArray);
        updateParameterListTable();
      }
    });
  });

function updateRequirementListTable(tableId, tableData) {
  console.log(
    `updateRequirementListTable(${tableId}, tableData), selectedReq=${globalSelectedRequirement}, tableId=${tableId}`
  );

  rqmtViewList = document
    .getElementById(tableId)
    .getElementsByTagName("tbody")[0];

  if (globalSelectedRequirement == 0) {
    selectedVerificationListData = verificationListData;
    document.getElementById("rl2").classList.add("hide");
    for (let i = 0; i < rqmtViewList.rows.length; i++) {
      rqmtViewList.rows[i].classList.remove("active");
    }
    rqmtDetails = document.getElementsByClassName("rqmt-detail");
    for (let i = 0; i < rqmtDetails.length; i++) {
      rqmtDetails[i].classList.remove("hide");
    }
  } else {
    document.getElementById("rl2").classList.remove("hide");
    for (let i = 0; i < rqmtViewList.rows.length; i++) {
      rqmtViewList.rows[i].classList.remove("active");
      if (
        rqmtViewList.rows[i].cells[0].innerText == globalSelectedRequirement
      ) {
        rqmtViewList.rows[i].classList.add("active");
        globalSelectedRequirementName = rqmtViewList.rows[i].cells[1].innerText;
      }
    }
    rqmtDetails = document.getElementsByClassName("rqmt-detail");
    for (let i = 0; i < rqmtDetails.length; i++) {
      rqmtDetails[i].classList.add("hide");
    }
  }

  testString = "";
  for (let rqmt in tableData) {
    if (tableData[rqmt]["fail"] == "0") {
      resultBadge = passBadge;
    } else {
      resultBadge = failBadge;
    }
    if (
      globalSelectedRequirement == tableData[rqmt]["number"] &&
      tableId == "rqmt-view-list"
    ) {
      testString += `<tr class="active" onclick="selectRequirement(${tableData[rqmt]["number"]})">
            <td class="number-col">${tableData[rqmt]["number"]}</td>
            <td>${tableData[rqmt]["title"]}</td>
            <td>${tableData[rqmt]["pass"]}</td>
            <td>${tableData[rqmt]["fail"]}</td>
            ${resultBadge}</tr>`;
    } else {
      testString += `<tr onclick="selectRequirement(${tableData[rqmt]["number"]})">
            <td class="number-col">${tableData[rqmt]["number"]}</td>
            <td>${tableData[rqmt]["title"]}</td>
            <td>${tableData[rqmt]["pass"]}</td>
            <td>${tableData[rqmt]["fail"]}</td>
            ${resultBadge}</tr>`;
    }
  }
  var activeTableBody = document
    .getElementById(tableId)
    .getElementsByTagName("tbody")[0];
  activeTableBody.innerHTML = testString;
}
function formatReq(requirement) {
  reqString = `<tr> <td>${requirement["title"]}</td>`;
  if (requirement["result"] == "PASSED") {
    reqString += `${passValue(requirement["value"])} ${passBadge}</tr>`;
  } else {
    reqString += `${failValue(requirement["value"])} ${failBadge}</tr>`;
  }
  return reqString;
}

function updateTestDetailTable() {
  testString = "";
  for (let index in testListData) {
    testListData;
    testNumber = testListData[index]["number"];
    if (index == 0) {
      testString += `<div id="test${testNumber}" class="test-info">`;
    } else {
      testString += `<div id="test${testNumber}" class="test-info hide">`;
    }
    testString += `<div class="tile-title">TEST DETAIL : ${testListData[index]["title"]} </div>`;
    testString += `<p>${testListData[index]["description"]}</p>`;

    if (testListData[index]["result"] == "ABORTED") {
      testString += `<p style="color:red">Test was aborted and did not complete, refer to the test logs for error details.</p>`;
    }

    testString += `<table class="test-detail-table">
                        <thead>
                            <tr>
                                <th class="number-col">#</th>
                                <th>Step</th>
                                <th class="status-col">Status</th>
                            </tr>
                        </thead>
                        <tbody id="test1_steps">`;

    let stepCount = 1;
    for (let step in testListData[index]["steps"]) {
      stepNumber = stepCount;
      stepCount = stepCount + 1;
      testString += ` <tr>
                                <td class="number-col">${stepNumber}</td>
                                <td><p style="padding:0; margin: 0;margin-bottom:6px;"> ${testListData[index]["steps"][step]["title"]}</p>
                                <div class="test_detail" style="margin-bottom:6px;margin-left:20px;">
                                    <p> ${testListData[index]["steps"][step]["description"]}</p>`;

      if (testListData[index]["steps"][step]["verifications"].length > 0) {
        //                testString += `<table style="width:90%!important;margin-bottom:6px;">
        testString += `<table>

                                                <thead>
                                                    <tr>
                                                        <th style="width:75%">Requirement</th>
                                                        <th style="width:100px;">Value</th>
                                                        <th class="status-col">Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>`;
        for (let ver in testListData[index]["steps"][step]["verifications"]) {
          testString += formatReq(
            testListData[index]["steps"][step]["verifications"][ver]
          );
        }
        testString += `</tbody></table>`;
      }
      testString += `</div></td>`;

      if (testListData[index]["steps"][step]["result"] == "PASSED") {
        testString += `${passBadge}`;
      } else {
        testString += `${failBadge}`;
      }
    }
    testString += `</table></div>`;
  }
  console.log(testString);
  document.getElementById("test-list-details").innerHTML = testString;
}

function updateTestListTable(tableId, tableData) {
  console.log(`updateTestListTable(${tableId}, tableData)`);

  testString = "";
  for (let test in tableData) {
    let resultBadge = failBadge;
    if (tableData[test]["result"] == "PASSED") {
      resultBadge = passBadge;
    }
    if (tableData[test]["result"] == "SKIPPED") {
      resultBadge = skipBadge;
    }

    if (
      globalSelectedTest == tableData[test]["number"] &&
      tableId == "test-view-list"
    ) {
      testString += `
            <tr class="active" onclick="selectTest(${tableData[test]["number"]})">
            <td class="number-col">${tableData[test]["number"]}</td>
            <td>${tableData[test]["title"]}</td>
            ${resultBadge}</tr>`;
    } else {
      testString += `
            <tr onclick="selectTest(${tableData[test]["number"]})">
            <td class="number-col">${tableData[test]["number"]}</td>
            <td>${tableData[test]["title"]}</td>
            ${resultBadge}</tr>`;
    }
  }
  const activeTable = document.getElementById(tableId);
  var activeTableBody = activeTable.getElementsByTagName("tbody")[0];
  activeTableBody.innerHTML = testString;
}

function updateVerificationListTable(tableData) {
  console.log(`updateVerificationListTable(tableData)`);
  let testString = "";
  for (let index in tableData) {
    console.log(tableData[index]["value"]);

    if (
      globalSelectedRequirement == 0 ||
      tableData[index]["title"] == globalSelectedRequirementName
    ) {
      testString += `<tr>
                        <td class="text-center">${tableData[index]["number"]}</td>
                        <td>${tableData[index]["title"]}</td>`;

      if (tableData[index]["result"] == "PASSED") {
        testString += `${passValue(tableData[index]["value"])}</td>
                        <td class="text-center">${tableData[index]["test number"]
          }</td>
                        <td>${tableData[index]["test"]}</td>
                        ${passBadge}</tr>`;
      } else {
        testString += `${failValue(tableData[index]["value"])}</td>
                        <td class="text-center">${tableData[index]["test number"]
          }</td>
                        <td>${tableData[index]["test"]}</td>
                        ${failBadge}</tr>`;
      }
    }
  }
  document
    .getElementById("rqmt-verifications")
    .getElementsByTagName("tbody")[0].innerHTML = testString;
}

function updateHostListTable(
  parameters,
  compareParameters,
  systemData,
  compareSystemData
) {
  if (compareSystemData !== null) {
    document.getElementById("host-parameters-compare").classList.remove("hide");
    var activeTableBody = document
      .getElementById("host-parameters-compare")
      .getElementsByTagName("tbody")[0];
    activeTableBody.innerHTML = `
            <tr>
                <td>Date</td>
                <td>${systemData["date"]}</td>
                <td>${compareSystemData["date"]}</td>
            </tr>
            <tr>
                <td>Hostname</td>
                <td>${systemData["hostname"]} </td>
                <td>${compareSystemData["hostname"]} </td>
            </tr>
            <tr>
                <td>Manufacturer</td>
                <td>${systemData["manufacturer"]} </td>
                <td>${compareSystemData["manufacturer"]} </td>
            </tr>
            <tr>
                <td>Model</td>
                <td>${systemData["model"]}</td>
                <td>${compareSystemData["model"]}</td>
            </tr>
            <tr>
                <td>BIOS Version</td>
                <td>${systemData["bios version"]}
                <td>${compareSystemData["bios version"]}
            <tr>
                <td>OS</td>
                <td>${systemData["os"]}</td>
                <td>${compareSystemData["os"]}</td>
            </tr>
            <tr>
                <td>UUID</td>
                <td> ${systemData["uuid"]}</td>
                <td> ${compareSystemData["uuid"]}</td>
            </tr>
        `;
  } else {
    document.getElementById("host-parameters").classList.remove("hide");
    var activeTableBody = document
      .getElementById("host-parameters")
      .getElementsByTagName("tbody")[0];
    activeTableBody.innerHTML = `
            <tr>
                <td>Date</td>
                <td>${systemData["date"]}</td>
            </tr>
            <tr>
                <td>Hostname</td>
                <td>${systemData["hostname"]} </td>
            </tr>
            <tr>
                <td>Manufacturer</td>
                <td>${systemData["manufacturer"]} </td>
            </tr>
            <tr>
                <td>Model</td>
                <td>${systemData["model"]}</td>
            </tr>
            <tr>
                <td>BIOS Version</td>
                <td>${systemData["bios version"]}
            <tr>
                <td>OS</td>
                <td>${systemData["os"]}</td>
            </tr>
            <tr>
                <td>UUID</td>
                <td> ${systemData["uuid"]}</td>
            </tr>
        `;
  }
}

function updateErrorLogTable() {
  const searchValue = document.getElementById("log-search").value.toLowerCase();
  var activeTableBody = document
    .getElementById("error-entries")
    .getElementsByTagName("tbody")[0];
  var mystring = ""; // load to string because faster

  console.log("update error log with search value " + searchValue);

  var filteredData = [];
  for (var i in errorLogArray) {
    let hasValue = false;
    for (const [name, value] of Object.entries(errorLogArray[i])) {
      if (name != undefined && value.toLowerCase().includes(searchValue)) {
        hasValue = true;
      }
    }
    if (hasValue) {
      filteredData.push(errorLogArray[i]);
    }
  }
  for (var i in filteredData) {
    mystring += `<tr>
            <td>${filteredData[i]["Error Count"]}</td>
            <td>${filteredData[i]["Command ID"]}</td>
            <td>${filteredData[i]["Command Specific Info"]}</td>
            <td>${filteredData[i]["Namespace"]}</td>
            <td>${filteredData[i]["Status Field"]}</td>
            <td>${filteredData[i]["Vendor Specific Info"]}</td>
            <td>${filteredData[i]["Submission Queue ID"]}</td>
            <td>${filteredData[i]["Byte Location"]}</td>
            <td>${filteredData[i]["Bit Location"]}</td>
            </tr>`;
  }
  activeTableBody.innerHTML = mystring;
}

function updateEventLogTable() {
  const searchValue = document.getElementById("log-search").value.toLowerCase();
  var activeTableBody = document
    .getElementById("event-entries")
    .getElementsByTagName("tbody")[0];
  var mystring = ""; // load to string because faster

  console.log("update event log with search value " + searchValue);

  var filteredData = [];
  for (var i in eventLogArray) {
    let hasValue = false;
    for (const [name, value] of Object.entries(eventLogArray[i])) {
      if (name != undefined && value.toLowerCase().includes(searchValue)) {
        hasValue = true;
      }
    }
    if (hasValue) {
      filteredData.push(eventLogArray[i]);
    }
  }
  for (var i in filteredData) {
    let eventHealth = filteredData[i]["Health"];

    if (eventHealth.toLowerCase() == "good") {
      eventHealth = "";
    }

    mystring += `<tr>
            <td>${filteredData[i]["Entry"]}</td>
            <td>${filteredData[i]["Time"]}</td>
            <td>${filteredData[i]["Type"]}</td>
            <td>${eventHealth}</td>
            <td>${filteredData[i]["Details"]}</td>
            </tr>`;
  }
  activeTableBody.innerHTML = mystring;
}

function updateCommandLogTable() {
  const searchValue = document.getElementById("log-search").value.toLowerCase();
  var activeTableBody = document
    .getElementById("command-entries")
    .getElementsByTagName("tbody")[0];
  var mystring = ""; // load to string because faster

  console.log("update command log with search value " + searchValue);

  var filteredData = [];
  for (var i in commandLogArray) {
    let hasValue = false;
    for (const [name, value] of Object.entries(commandLogArray[i])) {
      if (name != undefined && value.toLowerCase().includes(searchValue)) {
        hasValue = true;
      }
    }
    if (hasValue) {
      filteredData.push(commandLogArray[i]);
    }
  }
  for (var i in filteredData) {
    mystring += `<tr>
            <td>${filteredData[i]["Type"]}</td>
            <td>${filteredData[i]["Supported"]}</td>
            <td>${filteredData[i]["Controller Capability Change (CCC)"]}</td>
            <td>${filteredData[i]["Logical Block Content Change (LBCC)"]}</td>
            <td>${filteredData[i]["Namespace Capability Change (NCC)"]}</td>
            <td>${filteredData[i]["Namespace Inventory Change (NIC)"]}</td>
            <td>${filteredData[i]["UUID Selection Supported"]}</td>
            <td>${filteredData[i]["Command Submission and Execution (CSE)"]}</td>
            </tr>`;
  }
  activeTableBody.innerHTML = mystring;
}

function updateDiagnosticLogTable() {
  const searchValue = document.getElementById("log-search").value.toLowerCase();
  var activeTableBody = document
    .getElementById("diagnostic-entries")
    .getElementsByTagName("tbody")[0];
  var mystring = ""; // load to string because faster

  console.log(
    "update diagnostic log with search value " +
    searchValue +
    " entries " +
    diagnosticLogArray.length
  );

  var filteredData = [];
  for (var i in diagnosticLogArray) {
    let hasValue = false;
    for (const [name, value] of Object.entries(diagnosticLogArray[i])) {
      if (name != undefined && value.toLowerCase().includes(searchValue)) {
        hasValue = true;
      }
    }
    if (hasValue) {
      filteredData.push(diagnosticLogArray[i]);
    }
  }
  for (var i in filteredData) {
    mystring += `<tr>
            <td>${filteredData[i]["Entry"]}</td>
            <td>${filteredData[i]["Power On Hours"]}</td>
            <td>${filteredData[i]["Type"]}</td>
            <td>${filteredData[i]["Result"]}</td>
            <td>${filteredData[i]["Segment Number"]}</td>
            <td>${filteredData[i]["Namespace ID"]}</td>
            <td>${filteredData[i]["Failing LBA"]}</td>
            <td>${filteredData[i]["Status Code"]}</td>
            <td>${filteredData[i]["Status Code Type"]}</td>
        </tr>`;
  }
  activeTableBody.innerHTML = mystring;
}

function updateParameterListTable() {
  const value = document.getElementById("parameter-search").value.toLowerCase();
  var mystring = ""; // load to string because faster
  var filteredData = [];

  for (var i in parameterArray) {
    let hasValue = false;
    if (
      parameterArray[i].name != undefined &&
      parameterArray[i].name.toLowerCase().includes(value)
    ) {
      hasValue = true;
    }
    if (
      parameterArray[i].description != undefined &&
      parameterArray[i].description.toLowerCase().includes(value)
    ) {
      hasValue = true;
    }
    if (
      parameterArray[i].value != undefined &&
      parameterArray[i].value.toLowerCase().includes(value)
    ) {
      hasValue = true;
    }
    if (hasValue) {
      filteredData.push(parameterArray[i]);
    }
  }

  console.log("Updating parameter table");
  console.log(
    "  Search: " +
    value +
    " filtered parameters from " +
    parameterArray.length +
    " to " +
    filteredData.length
  );

  if (compareParameters !== null) {
    document
      .getElementById("device-parameters-compare")
      .classList.remove("hide");
    var activeTableBody = document
      .getElementById("device-parameters-compare")
      .getElementsByTagName("tbody")[0];
    activeTableBody.innerHTML = "";
    for (var i in filteredData) {
      mystring += `<tr>
                <td>${filteredData[i].name}</td>
                <td>${filteredData[i].value}</td>
                <td>${filteredData[i].change}</td>
                <td>${filteredData[i].description}</td>
                </tr>`;
    }
  } else {
    document.getElementById("device-parameters").classList.remove("hide");
    var activeTableBody = document
      .getElementById("device-parameters")
      .getElementsByTagName("tbody")[0];
    activeTableBody.innerHTML = "";
    for (var i in filteredData) {
      console.log(
        "Adding filter " + filteredData[i].name + "  " + filteredData[i].value
      );
      mystring += `<tr>
                <td>${filteredData[i].name}</td>
                <td>${filteredData[i].value}</td>
                <td>${filteredData[i].description}</td>
                </tr>`;
    }
  }
  activeTableBody.innerHTML = mystring;
}

function updateData() {
  console.log("Updating data for active NVMe " + activeNvme);

  systemData = allData[activeNvme]["system"];
  parameterDictionary = allData[activeNvme]["parameters"];
  commandLogArray = allData[activeNvme]["command log"];
  diagnosticLogArray = allData[activeNvme]["self-test log"];
  errorLogArray = allData[activeNvme]["error log"];
  eventLogArray = allData[activeNvme]["event log"];
  healthDictionary = allData[activeNvme]["health"];

  parameterArray = [];
  allParametersList = {};

  for (const [name, value] of Object.entries(parameterDictionary)) {
    allParametersList[name] = value["value"];
    parameterArray.push(parameterDictionary[name]);
  }
  if (globalParameterView != "all") {
    parameterArray = [];
    for (let i = 0; i < filters[globalParameterView].length; i++) {
      let parameter_name = filters[globalParameterView][i];
      if (parameter_name in parameterDictionary) {
        var value = parameterDictionary[parameter_name]["value"];
        var description = parameterDictionary[parameter_name]["description"];
        parameterArray.push({
          name: parameter_name,
          value: value,
          description: description,
          change: "",
        });
      }
    }
  }
  updateCommandLogTable();
  updateErrorLogTable();
  updateEventLogTable();
  updateDiagnosticLogTable();
  updateParameterListTable();
  updateHostListTable(
    parameterArray,
    compareParameters,
    systemData,
    compareSystemData
  );

  if (testView == true) {
    updateTestListTable("test-list", testListData);
    updateTestListTable("test-view-list", testListData);
    updateRequirementListTable("rqmt-list", rqmtListData);
    updateRequirementListTable("rqmt-view-list", rqmtListData);
    updateVerificationListTable(selectedVerificationListData);
    updateTestDetailTable();
  } else {
    updateHealthSection();
  }
}
