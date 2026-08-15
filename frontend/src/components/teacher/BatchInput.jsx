import React, { Component } from "react";
import { Card, Form } from 'react-bootstrap';
import serverRequest from "../../helper/serverRequest";
import * as XLSX from 'xlsx';
import { AuthContext } from "../AuthContext";

export default class BatchInput extends Component {
    static contextType = AuthContext;

    constructor(props) {
        super(props);
        this.serverURL = 'http://localhost:8000';
        this.subjectCode = props.subjectCode;
        this.subjectId = props.subjectId;
        this.deptId = props.deptId;
        this.classId = props.classId;
        this.batch = props.batch;
        this.state = { data: null, students: [] };
    }

    async componentDidMount() {
        console.log("Called APIs: " + this.serverURL + '/documents/Students');
        let students = await (await serverRequest(this.serverURL + '/documents/Student')).json();
        this.setState({ students: students, });
    }

    addData() {
        const { user } = this.context;
        const data = this.state.data;
        if (!data) return;

        const workbook = XLSX.read(data);
        const worksheet = workbook.Sheets[workbook.SheetNames[0]];
        const jsonData = XLSX.utils.sheet_to_json(worksheet, {
            header: 2,
            defval: "",
        });

        jsonData.map(async (entry) => {
            let marksGained = {};
            for (let key of Object.keys(entry)) {
                if (key.includes('/')) {
                    let splitKey = key.split('/');
                    if (!(splitKey[0] in marksGained))
                        marksGained[splitKey[0]] = {};
                    marksGained[splitKey[0]][splitKey[1]] = entry[key];
                }
                if (['SEE', 'CIE'].includes(key.trim()))
                    marksGained[key] = entry[key];
            }

            let studentId;
            let student = await (await serverRequest(this.serverURL + "/documents/Student", "POST", { searchObj: { USN: entry["USN"] } })).json();

            if (!student.length) {
                if (user.userType == "Admin") {
                    let studentRes = await serverRequest(this.serverURL + "/documents/Student/add", "POST", {
                        "Student Name": entry["Student Name"],
                        USN: entry["USN"],
                        "Admission Year": this.batch,
                        Batch: this.batch,
                        Department: this.deptId
                    });

                    if (studentRes.status == 200) {
                        studentId = await studentRes.text();
                        console.log("Inserted ", studentId);
                    }

                    await serverRequest(this.serverURL + "/documents/Class Allocation/add", "POST", { Class: this.classId, Student: studentId });
                }
                else return;
            }
            else
                studentId = student[0]._id;

            let marks = await (await serverRequest(this.serverURL + "/documents/Marks", "POST", { searchObj: { Subject: this.subjectId, Student: studentId } })).json();

            let message = { Marks: { Student: studentId, Subject: this.subjectId, "Marks Gained": marksGained } };
            if (marks.length)
                message.Marks._id = marks[0]["_id"];
            serverRequest(this.serverURL + "/Marks", marks.length ? "PUT" : "POST", message)
                .then(async (res) => {
                    if (res.status == 200) console.log("Inserted/Updated ", message);
                    else throw res;
                })
                .catch(err => console.error(err));
        })
    }

    async uploadFile(event) {
        let file = event.target.files[0];
        const data = await file.arrayBuffer();
        this.setState({ data: data, });
    }

    render() {
        return (
            <Card>
                <Card.Body className="py-1">
                    <Form className="row g-2">
                        <Form.Label className="col-md-5 col-form-label">Upload XLSX File For Batch Input: </Form.Label>
                        <div className="col-md-6">
                            <Form.Control className="col" type="file" name="file" required onChange={this.uploadFile.bind(this)} placeholder="Enter File" />
                        </div>
                        <button type="button" className="btn btn-primary col-md-1" onClick={() => this.addData()}>
                            <i className="fas fa-upload"></i>
                        </button>
                    </Form>
                </Card.Body>
            </Card>
        );
    }
}
