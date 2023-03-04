/* -------------------------------------------------------------------------------------------------
/ Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
/-------------------------------------------------------------------------------------------------
/ Main script for the html file creation.  First thing is check that testView is defined because
/ this indicates the data is there  Then init the html page
/
/ Version 3.5.23 - Joe Jones
/ ------------------------------------------------------------------------------------------------- */
try {
  if (typeof testView === "undefined") {
    throw new Error("Expected data missing.  testView undefined");
  }

  console.log("Test View : " + testView);
  console.log("Active NVMe : " + activeNvme);
  console.log("Number of NVMe : " + Object.entries(allData).length);

  createParameterViewDropDown();

  // Run for testnvme command

  if (testView == true) {
    const viewItems = document.getElementsByClassName("view-only");
    for (let i = 0; i < viewItems.length; i++) {
      viewItems[i].classList.add("hide");
    }
    document.getElementById("tested-nvme").innerHTML = activeNvme;

    if (info["result"] == "FAILED") {
      document.getElementById(
        "suite-name"
      ).innerHTML = `${info["title"]} Test Suite <span class="result-badge fail">FAIL</span>`;
    } else {
      document.getElementById(
        "suite-name"
      ).innerHTML = `${info["title"]} Test Suite <span class="result-badge pass">PASS</span>`;
    }

    var selectedVerificationListData = verificationListData;
    var sortedRqmtList = rqmtListData;
    var sortedTestList = testListData;
    var globalSelectedRequirementName = "";

    /* TODO Reduce size by ony using info needed */

    const test = info["summary"]["tests"];
    const rqmt = info["summary"]["rqmts"];
    const ver = info["summary"]["verifications"];

    /* Update Summary Section */

    document.getElementById("name").innerHTML = `${info["title"]}`;
    document.getElementById("id").innerHTML = `${info["id"]}`;
    document.getElementById("script version").innerHTML = `${info["script version"]}`;

    document.getElementById("model").innerHTML = `${info["model"]}`;
    document.getElementById("system").innerHTML = `${info["system"]}`;
    document.getElementById("location").innerHTML = `${info["location"]}`;

    document.getElementById("start").innerHTML = `${info["start time"]}`;
    document.getElementById("end").innerHTML = `${info["end time"]}`;
    document.getElementById("duration").innerHTML = `${info["duration"]}`;

    document.getElementById("test donut footer total").innerHTML = `<b>${test.total}</b> Total`;
    document.getElementById("test donut footer").innerHTML = `<b>${test.pass}</b> passed, <b>${test.fail}</b> failed, <b>${test.skip}</b> skipped`;
    document.getElementById("rqmt donut footer total").innerHTML = `<b>${rqmt.total}</b> Total`;
    document.getElementById("rqmt donut footer").innerHTML = `<b>${rqmt.pass}</b> passed, <b>${rqmt.fail}</b> failed `;
    document.getElementById("ver donut footer total").innerHTML = `<b>${ver.total}</b> Total`;
    document.getElementById("ver donut footer").innerHTML = `<b>${ver.pass}</b> passed, <b>${ver.fail}</b> failed `;

    updateChart(
      document.getElementById("tests").getContext("2d"),
      ["Pass", "Fail", "Skip"],
      [test.pass, test.fail, test.skip]
    );
    updateChart(document.getElementById("requirements").getContext("2d"), ["Pass", "Fail"], [rqmt.pass, rqmt.fail]);
    updateChart(document.getElementById("verifications").getContext("2d"), ["Pass", "Fail"], [ver.pass, ver.fail]);
  }
  // run for viewnvme, checknvme commands
  else {
    const viewItems = document.getElementsByClassName("testview-only");
    for (let i = 0; i < viewItems.length; i++) {
      viewItems[i].classList.add("hide");
    }

    globalSelectedSection = "health";
    createNvmeDropDown();
  }

  /* Add functions to the sidebar navigvation icons */

  document.getElementById("sb-health").onclick = function () {
    gotoSection("health");
  };
  document.getElementById("sb-summary").onclick = function () {
    gotoSection("summary");
  };
  document.getElementById("sb-parameter").onclick = function () {
    gotoSection("parameter");
  };
  document.getElementById("sb-host").onclick = function () {
    gotoSection("host");
  };
  document.getElementById("sb-help").onclick = function () {
    gotoSection("help");
  };
  document.getElementById("sb-test").onclick = function () {
    gotoSection("test");
  };
  document.getElementById("sb-rqmt").onclick = function () {
    gotoSection("rqmt");
  };

  /* Add functions to the health tiles for view/checknvme */

  document.getElementById("usage-tile").onclick = function () {
    setParameterView("usage");
  };
  document.getElementById("smart-tile").onclick = function () {
    setParameterView("smart");
  };
  document.getElementById("diag-tile").onclick = function () {
    setParameterView("self-tests");
  };
  document.getElementById("throttle-tile").onclick = function () {
    setParameterView("throttle");
  };
  document.getElementById("pcibw-tile").onclick = function () {
    setParameterView("pci");
  };
  document.getElementById("temp-tile").onclick = function () {
    setParameterView("temperature");
  };
  document.getElementById("events-tile").onclick = function () {
    setParameterView("events");
  };

  /* Add functions to the parameter view buttons */

  document.getElementById("pv-summary").onclick = function () {
    setParameterView("summary");
  };
  document.getElementById("pv-all").onclick = function () {
    setParameterView("all");
  };
  document.getElementById("pv-smart").onclick = function () {
    setParameterView("smart");
  };
  document.getElementById("pv-firmware").onclick = function () {
    setParameterView("firmware");
  };
  document.getElementById("pv-throttle").onclick = function () {
    setParameterView("throttle");
  };

  /* Add functions to two search boxes */

  document.getElementById("log-search").onkeyup = function () {
    updateCommandLogTable();
    updateErrorLogTable();
    updateEventLogTable();
    updateDiagnosticLogTable();
  };
  document.getElementById("parameter-search").onkeyup = function () {
    updateParameterListTable();
  };

  gotoSection(globalSelectedSection);
  updateData();
} catch (err) {
  let myString = "FAILED TO CREATE HTML FILE<br><br>";
  myString += "Send developer this message and all files from the target directory<br><br>";
  myString += err.name + "<br>" + err.message + "<br>";
  err.stack.split("\n").forEach((element) => (myString += "<br>" + element));

  const viewItemsOff = document.getElementsByClassName("view-only");
  for (let i = 0; i < viewItemsOff.length; i++) {
    viewItemsOff[i].classList.add("hide");
  }
  const testviewItemsOff = document.getElementsByClassName("testview-only");
  for (let i = 0; i < testviewItemsOff.length; i++) {
    testviewItemsOff[i].classList.add("hide");
  }
  gotoSection("fatal", false);
  document.getElementById("fatal-error").innerHTML = myString;
}
