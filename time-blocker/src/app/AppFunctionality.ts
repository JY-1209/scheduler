export function test() {
  window.addEventListener("load", init);

  function init() {
    let addTodoBtn = <HTMLElement>document.getElementById("myDiv");
    addTodoBtn.addEventListener("click", add);
  }

  function add(event: Event) {
    console.log(event);
    let newTodoName = <HTMLElement>document.getElementById("newTodoEntry");
    let newTodoNameValue = newTodoName.getAttribute("value");

    if (newTodoNameValue !== "") {
      let newTodoCard = document.createElement("ul");
      console.log(newTodoNameValue);
    }
  }
}
