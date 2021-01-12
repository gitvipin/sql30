
// const userAction = async () => {
  async function userAction() {
    try {
      let res = await fetch('http://localhost:5649/tables/otp_code');
      let myJson = await res.json(); //extract JSON from the http response
      return myJson;
    } catch (error) {
      console.log(myJson);
    }
}


function generateTableHead(table, data) {
  let thead = table.createTHead();
  let row = thead.insertRow();
  for (let key of data) {
    let th = document.createElement("th");
    let text = document.createTextNode(key);
    th.appendChild(text);
    row.appendChild(th);
  }
}


async function generateTable(table, nodata) {
  let data = await userAction();
  for (let element of data) {
    let row = table.insertRow();
    for (key in element) {
      let cell = row.insertCell();
      let text = document.createTextNode(element[key]);
      cell.appendChild(text);
    }
  }
}


let table = document.querySelector("table");
let data = Object.keys(["header1", "header2"]);
generateTable(table, data);
generateTableHead(table, data);
