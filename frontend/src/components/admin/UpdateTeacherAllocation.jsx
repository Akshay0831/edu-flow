import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useNavigate, useParams } from "react-router-dom";
import { Card, Form, Button } from "react-bootstrap";
import serverRequest from "../../helper/serverRequest";

export default function UpdateTeacherAllocation() {

    const navigate = useNavigate();
    const { id } = useParams();
    const isUpdate = Boolean(id);
    document.title = (isUpdate ? "Update" : "Add") + " Teacher Allocation";

    const [classes, setClasses] = useState([]);
    const [classID, setClassID] = useState("");
    const [subjects, setSubjects] = useState([]);
    const [subjectID, setSubjectID] = useState("");
    const [teachers, setTeachers] = useState([]);
    const [teacherID, setTeacherID] = useState("");
    const [departments, setDepartments] = useState([]);
    const [departmentID, setDeparmentID] = useState("");

    let toasts = (message, type) => {
        type(message, {
            position: "top-center",
            autoClose: 2500,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true,
            progress: undefined,
            theme: "colored",
        });
    }

    useEffect(() => {
        const fetchData = async () => {
            if (isUpdate) {
                const teacherAllocData = (await (await serverRequest("http://localhost:8000/documents/Teacher Allocation")).json()).filter(doc => doc._id == id)[0];
                setClassID(teacherAllocData["Class"]);
                setSubjectID(teacherAllocData["Subject"]);
                setTeacherID(teacherAllocData["Teacher"]);
                setDeparmentID(teacherAllocData["Department"]);
            }

            setClasses(await (await serverRequest("http://localhost:8000/Class")).json());
            setSubjects(await (await serverRequest("http://localhost:8000/documents/Subject")).json());
            setTeachers(await (await serverRequest("http://localhost:8000/documents/Teacher")).json());
            setDepartments(await (await serverRequest("http://localhost:8000/documents/Department")).json());
        }
        fetchData();
    }, []);

    const onSubmitClicked = (event) => {
        event.preventDefault();
        let teacherAllocData = {
            "Teacher Allocation": {
                "Class": classID,
                "Subject": subjectID,
                "Teacher": teacherID,
                "Department": departmentID,
            }
        };
        if (isUpdate) teacherAllocData._id = id;
        serverRequest(`http://localhost:8000/Teacher Allocation`, isUpdate ? "PUT" : "POST", teacherAllocData)
            .then(async (res) => {
                if (!res.ok)
                    throw new Error(await res.json());
                navigate("/admin/collectionlist", { state: "Teacher Allocation", });
                toasts(`${(isUpdate ? "Updated" : "Added")} Teacher Allocation`, toast.success);
            }).catch(err => toasts(err.message, toast.error));
    }

    return (
        <main className="pt-5">
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">{isUpdate ? "Update" : "Add"} Teacher Allocation</Card.Header>
                    <Card.Body>
                        <Form onSubmit={onSubmitClicked}>
                            <Form.Group className="mb-3">
                                <Form.Label>Class: </Form.Label>
                                <Form.Select name="class" value={classID} onChange={(event) => setClassID(event.target.value)} required>
                                    <option value="">Select Class</option>
                                    {classes && classes.map((classObj) => {
                                        return <option key={classObj._id} value={classObj._id}>{`${classObj["Semester"]}${classObj["Section"]} (${classObj["Department"]["Department Name"]})`}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Subject: </Form.Label>
                                <Form.Select name="subject" value={subjectID} onChange={(event) => setSubjectID(event.target.value)} required>
                                    <option value="">Select Subject</option>
                                    {subjects.map((subj) => {
                                        return <option key={subj._id} value={subj._id}>{`${subj["Subject Name"]} (${subj["Subject Code"]})`}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Teacher: </Form.Label>
                                <Form.Select name="teacher" value={teacherID} onChange={(event) => setTeacherID(event.target.value)} required>
                                    <option value="">Select Teacher</option>
                                    {teachers.map((teacher) => {
                                        return <option key={teacher._id} value={teacher._id}>{`${teacher["Teacher Name"]} (${teacher["Mail"]})`}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Department: </Form.Label>
                                <Form.Select name="department" value={departmentID} onChange={(event) => setDeparmentID(event.target.value)} required>
                                    <option value="">Select Department</option>
                                    {departments.map((dept) => {
                                        return <option key={dept._id} value={dept._id}>{dept["Department Name"]}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Button variant="success" type="submit">Submit</Button>
                        </Form>
                    </Card.Body>
                </Card>
            </div>
        </main>
    )
}