import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Form, Button } from "react-bootstrap";
import serverRequest from "../../helper/serverRequest";

export default function UpdateTeacher() {

    const navigate = useNavigate();
    const { id } = useParams();
    const isUpdate = Boolean(id);
    document.title = (isUpdate ? "Update" : "Add") + " Teacher";

    const [departments, setDepartments] = useState([]);
    const [mail, setMail] = useState("");
    const [role, setRole] = useState("");
    const [teacherName, setTeacherName] = useState("");
    const [departmentId, setDepartmentID] = useState("");

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
                const teachersData = (await (await serverRequest("http://localhost:8000/documents/Teacher")).json()).filter(doc => doc._id == id)[0];
                console.log(teachersData);
                setMail(teachersData["Mail"]);
                setRole(teachersData["Role"]);
                setTeacherName(teachersData["Teacher Name"]);
                setDepartmentID(teachersData["Department"]);
            }

            const departmentsData = await (await serverRequest("http://localhost:8000/documents/Department")).json();
            setDepartments(departmentsData);
        }
        fetchData();
    }, []);

    const onSubmitClicked = (event) => {
        event.preventDefault();
        let teacher = {
            "Teacher": {
                "Mail": mail,
                "Role": role,
                "Teacher Name": teacherName,
                "Department": departmentId
            }
        }
        if (isUpdate) teacher._id = id;
        serverRequest(`http://localhost:8000/Teacher`, (isUpdate ? "PUT" : "POST"), teacher)
            .then(async (res) => {
                if (!res.ok)
                    throw new Error(await res.json());
                navigate("/admin/collectionlist", { state: "Teacher", });
                toasts(`${(isUpdate ? "Updated" : "Added")} Teacher`, toast.success);
            }).catch(err => toasts(err.message, toast.error));
    }

    return (
        <main className="pt-5">
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">{isUpdate ? "Update" : "Add"} Teacher</Card.Header>
                    <Card.Body>
                        <Form onSubmit={onSubmitClicked}>
                            <Form.Group className="mb-3">
                                <Form.Label>Mail Id:</Form.Label>
                                <Form.Control type="email" name="mail" id="mail" value={mail} placeholder={"Enter Mail Id"} onChange={(event) => { setMail(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Role:</Form.Label>
                                <Form.Select name="role" id="role" value={role} placeholder={"Select Role"} onChange={(event) => { setRole(event.target.value) }} required >
                                    <option value="">Select Role</option>
                                    <option>Regular</option>
                                    <option>Privileged</option>
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Teacher Name:</Form.Label>
                                <Form.Control type="text" name="teacherName" id="teacherName" value={teacherName} placeholder={"Enter Teacher Name"} onChange={(event) => { setTeacherName(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Department: </Form.Label>
                                <Form.Select name="department" value={departmentId} onChange={(event) => setDepartmentID(event.target.value)} required>
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