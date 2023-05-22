"use client";

import Image from "next/image";
import React from "react";
import "bootstrap/dist/css/bootstrap.css";
import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
import { faGripLinesVertical } from "@fortawesome/free-solid-svg-icons";
import { faCalendarDays } from "@fortawesome/free-solid-svg-icons";
import { faEdit } from "@fortawesome/free-solid-svg-icons";
import { faTrashAlt } from "@fortawesome/free-solid-svg-icons";
import { faHourglassHalf } from "@fortawesome/free-solid-svg-icons";

export default function Home() {
  let addTodoBtn = () => {
    console.log("addTodoBtn");
  };

  return (
    <section className="vh-100">
      <div className="container py-5 h-100">
        <div className="row d-flex justify-content-center align-items-center h-100">
          <div className="col">
            <div
              className="card"
              id="list1"
              style={{
                borderRadius: "0.75em",
                backgroundColor: "#eff1f2",
              }}
            >
              <div className="card-body py-4 px-4 px-md-5">
                <p className="h1 text-center mt-3 mb-4 pb-3 text-primary">
                  <i className="fas fa-check-square me-1"></i>
                  <u>Todo List</u>
                </p>

                <div className="pb-2">
                  <div className="card">
                    <div className="card-body">
                      <div className="d-flex flex-row align-items-center">
                        <input
                          type="text"
                          className="form-control form-control-lg"
                          id="newTodoEntry"
                          placeholder="Add new..."
                        />
                        <a
                          href="#!"
                          data-mdb-toggle="tooltip"
                          title="Set due date"
                        >
                          <i className="fas fa-calendar-alt fa-lg me-3"></i>
                        </a>
                        <div>
                          <button
                            type="button"
                            className="btn btn-primary"
                            id="addTodoBtn"
                            onClick={addTodoBtn}
                          >
                            Add
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                <hr className="my-4" />

                <div className="d-flex justify-content-end align-items-center mb-4 pt-2 pb-3">
                  <p className="small mb-0 me-2 text-muted">Filter</p>
                  <select className="select">
                    <option value="1">All</option>
                    <option value="2">Completed</option>
                    <option value="3">Active</option>
                    <option value="4">Has due date</option>
                  </select>
                  <p className="small mb-0 ms-4 me-2 text-muted">Sort</p>
                  <select className="select">
                    <option value="1">Added date</option>
                    <option value="2">Due date</option>
                  </select>
                  <a
                    href="#!"
                    style={{ color: "#23af89" }}
                    data-mdb-toggle="tooltip"
                    title="Ascending"
                  >
                    <i className="fas fa-sort-amount-down-alt ms-2"></i>
                  </a>
                </div>

                <ul className="list-group list-group-horizontal rounded-0">
                  <li className="list-group-item d-flex align-items-center ps-0 pe-3 py-1 rounded-0 border-0 bg-transparent">
                    <FontAwesomeIcon
                      className="fa-lg mr-2"
                      icon={faGripLinesVertical}
                      style={{ marginBottom: "0.125rem", cursor: "grab" }}
                    />
                  </li>
                  <li className="list-group-item d-flex align-items-center ps-0 pe-3 py-1 rounded-0 border-0 bg-transparent">
                    <div className="form-check">
                      <input
                        className="form-check-input"
                        style={{ transform: "scale(1.5)" }}
                        type="checkbox"
                        value=""
                        id="flexCheckChecked2"
                        aria-label="..."
                      />
                    </div>
                  </li>
                  <li className="list-group-item px-3 py-1 d-flex align-items-center flex-grow-1 border-0 bg-transparent">
                    <p className="lead fw-normal mb-0">Meditate</p>
                  </li>
                  <li className="list-group-item px-3 py-1 d-flex align-items-center border-0 bg-transparent">
                    <div className="py-2 px-3 border border-danger rounded-3 d-flex align-items-center bg-light">
                      <input type="time" />
                      <p className="small mb-0">
                        <a
                          href="#!"
                          title="Due on date"
                          style={{ display: "inline-block" }}
                        >
                          <FontAwesomeIcon
                            icon={faHourglassHalf}
                            className="me-2"
                            style={{ color: "#dc3545" }}
                          />
                        </a>
                        30 min.
                      </p>
                    </div>
                  </li>
                  <li className="list-group-item px-3 py-1 d-flex align-items-center border-0 bg-transparent">
                    <div className="py-2 px-2 border border-primary rounded-3 d-flex align-items-center bg-light">
                      <FontAwesomeIcon
                        icon={faCalendarDays}
                        style={{
                          color: "#0275d8",
                          marginBottom: "0.125rem",
                          marginRight: "0rem",
                        }}
                      />
                      <input type="date" id="datePicker" />
                    </div>
                  </li>
                  <li className="list-group-item px-3 pe-0 py-1 d-flex align-items-center rounded-0 border-0 bg-transparent">
                    <div className="d-flex flex-row justify-content-end align-items-center">
                      <a
                        href="#!"
                        className="text-danger"
                        data-mdb-toggle="tooltip"
                        title="Delete todo"
                      >
                        <FontAwesomeIcon
                          style={{ transform: "scale(1.25)" }}
                          icon={faTrashAlt}
                        />
                      </a>
                    </div>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
