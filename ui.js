"use strict";

(function () {
  window.addEventListener("load", init);

  function init() {
    document.getElementById("addTodoBtn").addEventListener("click", add);
  }

  function add(event) {
    let newTodoEntry = document.getElementById("newTodoEntry").value;

    if (newTodoEntry !== "") {
      let newTodoCard = document.createElement("ul");
      console.log(newTodoEntry);
    }
  }
})();
