/* -------------------------------------------------------------------------------------------------
/ Copyright(c) 2023 Joseph Jones,  MIT License @  https://opensource.org/licenses/MIT
/-------------------------------------------------------------------------------------------------
/ Functions to create NVMe and Parameter drop downs.
/
/ Version 3.5.23 - Joe Jones
/ ------------------------------------------------------------------------------------------------- */
const parameterDefaultOptions = ["summary", "smart", "firmware", "throttle", "all"];

const parameterDropdownParent = document.getElementById("pv-dropdown-parent");
var parameterDropdown = document.createElement("div");
var parameterDropdownItems = document.createElement("div");

const nvmeDropdownParent = document.getElementById("nvme-dropdown-parent");
var nvmeDropdown = document.createElement("div");
var nvmeDropdownItems = document.createElement("div");

const caretDown =
  '<svg style="margin-right:5px;margin-left: auto;" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-down-fill" viewBox="0 0 16 16"><path d="M7.247 11.14 2.451 5.658C1.885 5.013 2.345 4 3.204 4h9.592a1 1 0 0 1 .753 1.659l-4.796 5.48a1 1 0 0 1-1.506 0z"></path></svg>';
const caretUp =
  '<svg style="margin-right:5px;margin-left: auto;" xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" class="bi bi-caret-up-fill" viewBox="0 0 16 16"><path d="m7.247 4.86-4.796 5.481c-.566.647-.106 1.659.753 1.659h9.592a1 1 0 0 0 .753-1.659l-4.796-5.48a1 1 0 0 0-1.506 0z"></path></svg>';

function createNvmeDropDown() {
  var nvmeOptions = [];
  for (const [name, value] of Object.entries(allData)) {
    nvmeOptions.push(name);
  }
  nvmeDropdown.setAttribute("class", "nvme-dropdown");
  nvmeDropdown.innerHTML = nvmeOptions[0] + caretDown;
  nvmeDropdown.id = "nvme-dropdown";
  nvmeDropdownParent.appendChild(nvmeDropdown);

  nvmeDropdownItems.setAttribute("class", "nvme-dropdown-items hide");
  nvmeDropdownItems.id = "nvme-dropdown-items";
  for (let index = 0; index < nvmeOptions.length; index++) {
    console.log("Adding NVMe to drop-down: " + nvmeOptions[index]);
    var filterNvmeOption = document.createElement("DIV");
    filterNvmeOption.innerHTML = nvmeOptions[index];

    filterNvmeOption.addEventListener("click", function (event) {
      console.log("Change to nvme " + nvmeOptions[index]);
      document.getElementById("nvme-dropdown").innerHTML = this.innerHTML + caretDown;
      activeNvme = nvmeOptions[index];
      updateData();
      document.getElementById("nvme-dropdown").className = "nvme-dropdown  active";
    });
    nvmeDropdownItems.appendChild(filterNvmeOption);
  }
  nvmeDropdownParent.appendChild(nvmeDropdownItems);

  nvmeDropdown.addEventListener("click", function (event) {
    parameterDropdown.innerHTML = parameterDropdown.innerHTML.replace(caretUp, caretDown);
    parameterDropdownItems.classList.add("hide");

    event.stopPropagation();

    this.nextSibling.classList.toggle("hide");
    if (this.innerHTML.indexOf(caretDown) === -1) {
      this.innerHTML = this.innerHTML.replace(caretUp, caretDown);
    } else {
      this.innerHTML = this.innerHTML.replace(caretDown, caretUp);
    }
  });
}

function createParameterViewDropDown() {
  var parameterDropDownItems = [];
  for (const [name, value] of Object.entries(filters)) {
    if (false == parameterDefaultOptions.includes(name)) {
      parameterDropDownItems.push(name.toUpperCase());
    }
  }
  parameterDropdown.setAttribute("class", "param-select-dropdown ");
  parameterDropdown.innerHTML = `<span style= "margin-left: auto">${parameterDropDownItems[0]}</span>` + caretDown;
  parameterDropdown.id = "pv-dropdown";

  parameterDropdownItems.setAttribute("class", "param-select-dropdown-items hide");
  parameterDropdownItems.id = "pv-combo-holder";

  parameterDropdownParent.appendChild(parameterDropdown);

  for (let index = 0; index < parameterDropDownItems.length; index++) {
    console.log("Adding parameter select to drop-down: " + parameterDropDownItems[index]);
    var filterOption = document.createElement("DIV");
    filterOption.innerHTML = parameterDropDownItems[index];

    filterOption.addEventListener("click", function (event) {
      document.getElementById("pv-dropdown").innerHTML = `<span style= "margin-left: auto">${this.innerHTML}</span>` + caretDown;
      document.getElementById("pv-dropdown").className = "param-select-dropdown active";
      setParameterView(this.innerText)
    });
    parameterDropdownItems.appendChild(filterOption);
  }
  parameterDropdownParent.appendChild(parameterDropdownItems);

  parameterDropdown.addEventListener("click", function (event) {
    nvmeDropdown.innerHTML = nvmeDropdown.innerHTML.replace(caretUp, caretDown);
    nvmeDropdownItems.classList.add("hide");

    event.stopPropagation();
    this.nextSibling.classList.toggle("hide");
    if (this.innerHTML.indexOf(caretDown) === -1) {
      this.innerHTML = this.innerHTML.replace(caretUp, caretDown);
    } else {
      this.innerHTML = this.innerHTML.replace(caretDown, caretUp);
    }
  });
}

/* Clicking anywhere in the document closes all drop down */

document.onclick = function () {
  parameterDropdown.innerHTML = parameterDropdown.innerHTML.replace(caretUp, caretDown);
  parameterDropdownItems.classList.add("hide");
  nvmeDropdown.innerHTML = nvmeDropdown.innerHTML.replace(caretUp, caretDown);
  nvmeDropdownItems.classList.add("hide");
};
