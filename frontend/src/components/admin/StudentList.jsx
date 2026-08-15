import React, { Component, lazy } from "react";
const AccordionItem = lazy(() => import("../AccordionItem"));
import { InfinitySpin } from 'react-loader-spinner';
import { Link } from "react-router-dom";
import serverRequest from "../../helper/serverRequest";

export default class StudentList extends Component {

    async componentDidMount() {
        let data = await (await serverRequest("http://localhost:8000/Student/update")).json();
        this.setState({ Students: data });
        document.title = "Students by Class";
    }

    async deleteClicked(id) {
        let res = await serverRequest("http://localhost:8000/Student", "DELETE", { _id: id }, { "Content-type": "application/json; charset=UTF-8" });
        if (res.status == 200) {
            let stud = (this.state.Students).filter((doc) => doc._id !== id);
            this.setState({ Students: stud });
            this.forceUpdate(this.componentDidMount);
        }
    }

    render() {
        return (
            <main className="pt-5" >
                <div className="container">
                    <button className="btn btn-success">
                        <Link to={"/admin/Student/add"} style={{ textDecoration: 'none', color: 'white' }}> <i className="fas fa-solid fa-user-plus"></i> Add Student </Link>
                    </button>
                    <hr />
                    {this.state
                        ? (
                            <div className="accordion" id="DepartmentsAccordion">
                                {this.state.Students.map((dept, deptIndex) => {
                                    return (
                                        <AccordionItem
                                            key={dept._id}
                                            accHeadingId={dept["Department Name"]}
                                            accId="DepartmentsAccordion"
                                            targetAndControls={dept["Department Name"]}
                                            headContent={dept["Department Name"]}>
                                            <div className="accordion" id="ClassesAccordion">
                                                <h4>Classes</h4>
                                                {dept.Classes.map((classObj, classIndex) => {
                                                    return (
                                                        <AccordionItem
                                                            key={classObj.Section + classObj.Semester + "_" + dept._id}
                                                            accHeadingId={dept["Department Name"] + classObj.Semester + classObj.Section}
                                                            accId="ClassesAccordion"
                                                            targetAndControls={dept["Department Name"] + classObj.Semester + classObj.Section}
                                                            headContent={classObj.Semester + classObj.Section}>
                                                            <div className="accordion" id="StudentsAccordion">
                                                                <h4>Students</h4>
                                                                {classObj.Students.map((student, studentIndex) => {
                                                                    return (
                                                                        <AccordionItem
                                                                            key={student.USN}
                                                                            accHeading={student["Student Name"] + "(" + student.USN + ")"}
                                                                            accId="StudentsAccordion"
                                                                            targetAndControls={classObj.Section + classObj.Semester + "_" + student.USN}
                                                                            headContent={student["Student Name"] + " (" + student.USN + ")"}>
                                                                            <div className="accordion table-responsive" id="StudentsDetailsAccordion">
                                                                                <table className="table table-borderless">
                                                                                    <tbody>
                                                                                        <tr>
                                                                                            <td>Name:</td>
                                                                                            <td>{student["Student Name"]}</td>
                                                                                        </tr>
                                                                                        <tr>
                                                                                            <td>USN:</td>
                                                                                            <td>{student.USN}</td>
                                                                                        </tr>
                                                                                        <tr>
                                                                                            <td>Admission Year:</td>
                                                                                            <td>{student["Admission Year"]}</td>
                                                                                        </tr>
                                                                                        <tr>
                                                                                            <td>Batch:</td>
                                                                                            <td>{student.Batch}</td>
                                                                                        </tr>
                                                                                    </tbody>
                                                                                    <tfoot>
                                                                                        <tr className="text-center">
                                                                                            <td colSpan={2}>
                                                                                                <div className="btn-group">
                                                                                                    <button className="btn btn-warning py-1">
                                                                                                        <Link to={`/admin/student/update/${student._id}`}><i className="fa fa-pencil" aria-hidden="true" /></Link>
                                                                                                    </button>
                                                                                                    <button className="btn btn-danger" onClick={() => { this.deleteClicked(student._id) }}>
                                                                                                        <i className="fa fa-solid fa-user-minus" aria-hidden="true"></i>
                                                                                                    </button>
                                                                                                </div>
                                                                                            </td>
                                                                                        </tr>
                                                                                    </tfoot>
                                                                                </table>
                                                                            </div>
                                                                        </AccordionItem>
                                                                    );
                                                                })}
                                                            </div>
                                                        </AccordionItem>
                                                    );
                                                })}
                                            </div>
                                        </AccordionItem>
                                    )
                                })}
                            </div>)
                        : <div className='d-flex justify-content-center'><InfinitySpin color="#FFF" width='200' visible={true} /></div>
                    }
                </div>
            </main>
        );
    }
}