/*-------------------------------------------------------------------------------------
 Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
------------------------------------------------------------------------------------*/
let parameterData = summary
let selectedTest = 1
let selectedRequirement = 0
let selectedRequirementName = ""

const failBadge = `<td class="status-col"><span class="badge badge-fail">FAIL</span></td>`
const passBadge = `<td class="status-col"><span class="badge badge-pass">PASS</span></td>`
const skipBadge = `<td class="status-col"><span class="badge badge-skip">SKIP</span></td>`

function passValue(value) { return `<td>${value}</td>` }
function failValue(value) { return `<td style="color:red;font-weight:bold;">${value}</td>` }

document.querySelectorAll('.sort-list th').forEach(function (header, index) {
    header.addEventListener('click', function () {

        let tableData = parameterData
        const tableId = this.parentNode.parentNode.parentNode.id

        console.log(`Sort list on ${tableId} col: ${this.dataset.column}`)

        if (this.parentNode.parentNode.parentNode.classList.contains("test-list")) {
            sortedTestList = sortTableData(this.dataset, sortedTestList)
            updateTestListTable(this.parentNode.parentNode.parentNode.id, sortedTestList)
        }
        else if (this.parentNode.parentNode.parentNode.classList.contains("rqmt-list")) {
            sortTableData(this.dataset, sortedRqmtList)
            updateRequirementListTable(this.parentNode.parentNode.parentNode.id, sortedRqmtList)
        }
        else if (this.parentNode.parentNode.parentNode.classList.contains("verification-list")) {
            sortTableData(this.dataset, selectedVerificationListData)
            updateVerificationListTable(selectedVerificationListData)
        }
        else {
            sortTableData(this.dataset, parameterData)
            updateParameterListTable(parameterData)
        }
    })
})

function collapseTests(x) {
    document.getElementById("expanded").classList.add("d-none")
    document.getElementById("collapsed").classList.remove("d-none")
}

function donut_chart(element_by_id, labels, values) {
    let main_body = document.getElementById('mainbody');
    const tmpChart = new Chart(element_by_id, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    getComputedStyle(main_body).getPropertyValue("--pass-bg-color"),
                    getComputedStyle(main_body).getPropertyValue("--fail-bg-color"),
                    getComputedStyle(main_body).getPropertyValue("--skip-bg-color")
                ],
                hoverOffset: 4
            }]
        },
        options: {
            responsive: false,
            plugins: {
                legend: { display: true, position: 'right', labels: { boxWidth: 15 } },
                tooltip: {
                    callbacks: {
                        label: function(context, data) {
                                let label = context.label
                                let value = context.formattedValue;
                                let sum = 0
                                let dataArr = context.chart.data.datasets[0].data
                                dataArr.map(data => {sum += Number(data) })
                                return label + ": " + value + " (" + (value*100/sum).toFixed(1) + '%)'
                        }
                    }
                }
            }
        }
    })
};

function expandTests(x) {
    document.getElementById("collapsed").classList.add("d-none")
    document.getElementById("expanded").classList.remove("d-none")
}

function formatReq(requirement) {
    reqString = `<tr> <td>${requirement["title"]}</td>`
    if (requirement["result"] == "PASSED") {
        reqString += `${passValue(requirement["value"])} ${passBadge}</tr>`
    }
    else {
        reqString += `${failValue(requirement["value"])} ${failBadge}</tr>`
    }
    return reqString
}

function setRqmt(newRequirement) {
    selectedRequirement = newRequirement
    updateRequirementListTable("rqmt list", sortedRqmtList)
    updateRequirementListTable("rqmt view list", sortedRqmtList)
    updateVerificationListTable(selectedVerificationListData)
}

function setRqmtView(newRequirement) {
    setRqmt(newRequirement)
    toggleView('rqmt-view');
}

function setTestView(newselectedTest) {
    selectedTest = newselectedTest
    var testViewListBody = document.getElementById('test view list').getElementsByTagName('tbody')[0];

    for (let i = 0; i < testViewListBody.rows.length; i++) {
        testViewListBody.rows[i].classList.remove("active")
        if (testViewListBody.rows[i].cells[0].innerHTML == selectedTest) {
            testViewListBody.rows[i].classList.add("active")
        }
    }
    testDetails = document.getElementsByClassName("test-detail")
    for (let i = 0; i < testDetails.length; i++) {
        testDetails[i].classList.add("d-none")
    }

    let activeDetail = document.getElementById(`test${selectedTest}`)
    activeDetail.classList.remove("d-none")
    toggleView('test-view');
}

function sortTableData(dataset, tableData) {
    let column = dataset.column
    let order = dataset.order
    if (order === 'desc') {
        dataset.order = "asc";
        tableData = tableData.sort((a, b) =>
            a[column] > b[column] ? 1 : a[column] == b[column] && a['number'] > b['number'] ? 1 : -1
        )
    } else {
        dataset.order = "desc";
        tableData = tableData.sort((a, b) =>
            a[column] < b[column] ? 1 : a[column] == b[column] && a['number'] < b['number'] ? 1 : -1
        )
    }
    return tableData
}

function toggleView(newView) {
    allViews = document.getElementsByClassName("view");
    for (let i = 0; i < allViews.length; i++) {
        allViews[i].classList.remove("d-block")
        allViews[i].classList.add("d-none")
    }
    activeView = document.getElementById(newView);
    activeView.classList.remove("d-none")
    activeView.classList.add("d-block")
}

function updateHostListTable(info, compareInfo, systemData, compareSystemData) {
    if (compareSystemData !== null) {
        document.getElementById("host parameters compare").classList.remove("d-none")
        var activeTableBody = document.getElementById("host parameters compare").getElementsByTagName('tbody')[0];
        activeTableBody.innerHTML = `
            <tr>
                <td>Hostname</td>
                <td>${systemData['hostname']} </td>
                <td>${compareSystemData['hostname']} </td>
            </tr>
            <tr>
                <td>Manufacturer</td>
                <td>${systemData['manufacturer']} </td>
                <td>${compareSystemData['manufacturer']} </td>
            </tr>
            <tr>
                <td>Model</td>
                <td>${systemData['model']}</td>
                <td>${compareSystemData['model']}</td>
            </tr>
            <tr>
                <td>BIOS Version</td>
                <td>${systemData['bios version']}
                <td>${compareSystemData['bios version']}
            <tr>
                <td>OS</td>
                <td>${systemData['os']}</td>
                <td>${compareSystemData['os']}</td>
            </tr>
            <tr>
                <td>UUID</td>
                <td> ${systemData['uuid']}</td>
                <td> ${compareSystemData['uuid']}</td>
            </tr>
            <tr>
                <td>NVMe</td>
                <td>${info['nvme']['description']}</td>
                <td>${compareInfo['nvme']['description']}</td>
            </tr>
            <tr>
                <td>Date</td>
                <td>${info['_metadata']['date']}</td>
                <td>${compareInfo['_metadata']['date']}</td>
            </tr>
        `
    }
    else {
        document.getElementById("host parameters").classList.remove("d-none")
        var activeTableBody = document.getElementById("host parameters").getElementsByTagName('tbody')[0];
        activeTableBody.innerHTML = `
            <tr>
                <td>Hostname</td>
                <td>${systemData['hostname']} </td>
            </tr>
            <tr>
                <td>Manufacturer</td>
                <td>${systemData['manufacturer']} </td>
            </tr>
            <tr>
                <td>Model</td>
                <td>${systemData['model']}</td>
            </tr>
            <tr>
                <td>BIOS Version</td>
                <td>${systemData['bios version']}
            <tr>
                <td>OS</td>
                <td>${systemData['os']}</td>
            </tr>
            <tr>
                <td>UUID</td>
                <td> ${systemData['uuid']}</td>
            </tr>
            <tr>
                <td>NVMe</td>
                <td>${model}</td>
            </tr>
            <tr>
                <td>Date</td>
                <td>${host_date}</td>
            </tr>
        `
    }
}

function updateParameterListTable(userData) {
    if (userData === null) { userData = parameterData; console.info("updateParameterListTable with size is null"); }
    else { parameterData = userData; console.info("updateParameterListTable with size " + parameterData.length); }

    const value = document.getElementById("parameter-search").value

    var filteredData = []
    for (var i in userData) {
        let hasValue = false;
        if (userData[i].name != undefined && userData[i].name.toLowerCase().includes(value)) { hasValue = true; }
        if (userData[i].description != undefined && userData[i].description.toLowerCase().includes(value)) { hasValue = true; }
        if (userData[i].value != undefined && userData[i].value.toLowerCase().includes(value)) { hasValue = true; }
        if (hasValue) { filteredData.push(userData[i]) }
    }

    let mystring = "";  // load to string because faster
    if (compareInfo !== null) {
        document.getElementById("device parameters compare").classList.remove("d-none")
        var activeTableBody = document.getElementById("device parameters compare").getElementsByTagName('tbody')[0];
        activeTableBody.innerHTML = '';
        for (var i in filteredData) {
            mystring += `<tr>
                <td>${filteredData[i].name}</td>
                <td>${filteredData[i].value}</td>
                <td>${filteredData[i].change}</td>
                <td>${filteredData[i].description}</td>
                </tr>`
        }
    }
    else {
        document.getElementById("device parameters").classList.remove("d-none")
        var activeTableBody = document.getElementById("device parameters").getElementsByTagName('tbody')[0];
        activeTableBody.innerHTML = '';
        for (var i in filteredData) {
            mystring += `<tr>
                <td>${filteredData[i].name}</td>
                <td>${filteredData[i].value}</td>
                <td>${filteredData[i].description}</td>
                </tr>`
        }
    }
    activeTableBody.innerHTML = mystring;
}

function updateRequirementListTable(tableId, tableData) {
    console.log(`updateRequirementListTable(${tableId}, tableData), selectedReq=${selectedRequirement}, tableId=${tableId}`)

    rqmtViewList = document.getElementById(tableId).getElementsByTagName('tbody')[0];

    if (selectedRequirement == 0) {
        selectedVerificationListData = verificationListData
        document.getElementById('rl2').classList.add('d-none')
        for (let i = 0; i < rqmtViewList.rows.length; i++) {
            rqmtViewList.rows[i].classList.remove("active")
        }
        rqmtDetails = document.getElementsByClassName("rqmt-detail")
        for (let i = 0; i < rqmtDetails.length; i++) {
            rqmtDetails[i].classList.remove("d-none")
        }
    }
    else {
        document.getElementById('rl2').classList.remove('d-none')
        for (let i = 0; i < rqmtViewList.rows.length; i++) {
            rqmtViewList.rows[i].classList.remove("active")
            //                    if (rqmtViewList.rows[i].cells[0].innerHTML == selectedRequirement) {

            if (rqmtViewList.rows[i].cells[0].innerText == selectedRequirement) {

                console.log(`found it ${selectedRequirement}`)
                rqmtViewList.rows[i].classList.add("active")
                selectedRequirementName = rqmtViewList.rows[i].cells[1].innerText

            }
        }
        rqmtDetails = document.getElementsByClassName("rqmt-detail")
        for (let i = 0; i < rqmtDetails.length; i++) {
            rqmtDetails[i].classList.add("d-none")
        }
    }

    testString = ""
    for (let rqmt in tableData) {
        if (tableData[rqmt]["fail"] == "0") {
            resultBadge = passBadge
        }
        else {
            resultBadge = failBadge
        }
        if (selectedRequirement == tableData[rqmt]['number'] && tableId == "rqmt view list") {
            testString += `<tr class="active" onclick="setRqmtView(${tableData[rqmt]['number']})">
            <td class="number-col">${tableData[rqmt]['number']}</td>
            <td>${tableData[rqmt]["title"]}</td>
            <td>${tableData[rqmt]["pass"]}</td>
            <td>${tableData[rqmt]["fail"]}</td>
            ${resultBadge}</tr>`
        }
        else {
            testString += `<tr onclick="setRqmtView(${tableData[rqmt]['number']})">
            <td class="number-col">${tableData[rqmt]['number']}</td>
            <td>${tableData[rqmt]["title"]}</td>
            <td>${tableData[rqmt]["pass"]}</td>
            <td>${tableData[rqmt]["fail"]}</td>
            ${resultBadge}</tr>`
        }
    }
    var activeTableBody = document.getElementById(tableId).getElementsByTagName('tbody')[0]
    activeTableBody.innerHTML = testString
}

function updateTestDetailTable() {
    testString = ""
    for (let index in testListData) {
        testListData
        testNumber = testListData[index]['number']
        if (index == 0) {
            testString += `<div id="test${testNumber}" class="card test-detail"><div class="card-body text-left p-10">`
        }
        else {
            testString += `<div id="test${testNumber}" class="card test-detail d-none"><div class="card-body text-left p-10">`
        }
        testString += `<p class="card-title">TEST DETAIL : ${testListData[index]["title"]} </p>`
        testString += `<p>${testListData[index]["description"]}</p>`



        if (testListData[index]["result"] == "ABORTED") {
            testString += `<p style="color:red">Test was aborted and did not complete, refer to the test logs for error details.</p>`
        }

        testString += `<table class="table">
                        <thead>
                            <tr>
                                <th class="text-center" style="width:30px">#</th>
                                <th>Step</th>
                                <th class="text-center" style="width:60px">Status</th>
                            </tr>
                        </thead>
                        <tbody id="test1_steps">`

        let stepCount = 1
        for (let step in testListData[index]["steps"]) {
            stepNumber = stepCount
            stepCount = stepCount + 1
            testString += ` <tr>
                                <td class="text-center">${stepNumber}</td>
                                <td>${testListData[index]["steps"][step]["title"]}
                                <div class="test_detail collapse show">
                                    <p class="mt-0"> ${testListData[index]["steps"][step]["description"]}</p>`

            if (testListData[index]["steps"][step]["verifications"].length > 0) {
                testString += `<table class="table" style="width:80%!important">
                                                <thead>
                                                    <tr>
                                                        <th style="width:75%">Requirement</th>
                                                        <th style="width:100px;">Value</th>
                                                        <th class="status-col">Status</th>
                                                    </tr>
                                                </thead>
                                                <tbody>`
                for (let ver in testListData[index]["steps"][step]["verifications"]) {
                    testString += formatReq(testListData[index]["steps"][step]["verifications"][ver])
                }
                testString += `</tbody></table>`
            }
            testString += `</div></td>`

            if (testListData[index]["steps"][step]["result"] == "PASSED") {
                testString += `${passBadge}`
            }
            else {
                testString += `${failBadge}`
            }
        }
        testString += `</table></div></div>`
    }
    console.log(testString)
    document.getElementById('test-list-details').innerHTML = testString
}

function updateTestListTable(tableId, tableData) {
    console.log(`updateTestListTable(${tableId}, tableData)`)

    testString = ""
    for (let test in tableData) {
        let resultBadge = failBadge
        if (tableData[test]["result"] == "PASSED") {
            resultBadge = passBadge
        }
        if (tableData[test]["result"] == "SKIPPED") {
            resultBadge = skipBadge
        }

        if (selectedTest == tableData[test]['number'] && tableId == "test view list") {
            testString += `
            <tr class="active" onclick="setTestView(${tableData[test]['number']})">
            <td class="number-col">${tableData[test]['number']}</td>
            <td>${tableData[test]['title']}</td>
            ${resultBadge}</tr>`
        }
        else {
            testString += `
            <tr onclick="setTestView(${tableData[test]['number']})">
            <td class="number-col">${tableData[test]['number']}</td>
            <td>${tableData[test]['title']}</td>
            ${resultBadge}</tr>`
        }
    }
    const activeTable = document.getElementById(tableId)
    var activeTableBody = activeTable.getElementsByTagName('tbody')[0]
    activeTableBody.innerHTML = testString
}

function updateVerificationListTable(tableData) {
    console.log(`updateVerificationListTable(tableData)`)
    let testString = ""
    for (let index in tableData) {

        console.log(tableData[index]["value"])

        if ((selectedRequirement == 0) || (tableData[index]["title"] == selectedRequirementName)) {
            testString += `<tr>
                        <td class="text-center">${tableData[index]["number"]}</td>
                        <td>${tableData[index]["title"]}</td>`

            if (tableData[index]["result"] == "PASSED") {
                testString += `${passValue(tableData[index]["value"])}</td>
                        <td class="text-center">${tableData[index]["test number"]}</td>
                        <td>${tableData[index]["test"]}</td>
                        ${passBadge}</tr>`
            }
            else {
                testString += `${failValue(tableData[index]["value"])}</td>
                        <td class="text-center">${tableData[index]["test number"]}</td>
                        <td>${tableData[index]["test"]}</td>
                        ${failBadge}</tr>`
            }
        }
    }
    document.getElementById('rqmt verifications').getElementsByTagName('tbody')[0].innerHTML = testString
}
