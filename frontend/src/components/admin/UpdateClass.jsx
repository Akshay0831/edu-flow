import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useNavigate, useParams } from "react-router-dom";
import { Card, Form, Button } from "react-bootstrap";
import serverRequest from "../../helper/serverRequest";

export default function UpdateClass() {

    const navigate = useNavigate();
    const { id } = useParams();
    const isUpdate = Boolean(id);
    document.title = (isUpdate ? "Update" : "Add") + " Class";

    const [departments, setDepartments] = useState([]);
    const [departmentID, setDepartmentID] = useState("");
    const [semester, setSemester] = useState("");
    const [section, setSection] = useState("");

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
            // console.log((await (await serverRequest("http://localhost:8000/documents/Department")).json()).filter(doc => doc._id == "64256326539b7e514a91fe64" )[0]);
            if (isUpdate) {
                const classData = (await (await serverRequest("http://localhost:8000/documents/Class")).json()).filter(doc => doc._id == id)[0];
                console.log(classData);
                setDepartmentID(classData["Department"]);
                setSemester(classData["Semester"]);
                setSection(classData["Section"]);
            }

            const departmentsData = await (await serverRequest("http://localhost:8000/documents/Department")).json();
            setDepartments(departmentsData);
        }
        fetchData();
    }, []);

    const onSubmitClicked = (event) => {
        event.preventDefault();
        let classData = {
            "Class": {
                "Department": departmentID,
                "Semester": semester,
                "Section": section,
            }
        };
        if (isUpdate) classData._id = id;
        serverRequest(`http://localhost:8000/Class`, isUpdate ? "PUT" : "POST", classData, { "Content-Type": "application/json; charset=UTF-8" })
            .then(async (res) => {
                if (!res.ok)
                    throw new Error(await res.json());
                navigate("/admin/collectionlist", { state: "Class", });
                toasts(`${(isUpdate ? "Updated" : "Added")} Class`, toast.success);
            }).catch(err => toasts(err.message, toast.error));
    }

    const handleDepartmentChange = (event) => setDepartmentID(event.target.value);

    return (
        <main className="pt-5">
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">{isUpdate ? "Update" : "Add"} Class</Card.Header>
                    <Card.Body>
                        <Form onSubmit={onSubmitClicked}>
                            <Form.Group className="mb-3">
                                <Form.Label>Department Name:</Form.Label>
                                <Form.Select name="department" value={departmentID} onChange={handleDepartmentChange}>
                                    <option value="">Select Department</option>
                                    {departments.map((dept) => {
                                        return <option key={dept._id} value={dept._id}>{dept["Department Name"]}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Semester: </Form.Label>
                                <Form.Control type="number" name="semester" id="semester" value={semester} placeholder={"Semester"} onChange={(event) => { setSemester(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Section: </Form.Label>
                                <Form.Control type="text" name="section" id="section" value={section} placeholder={"Section"} onChange={(event) => { setSection(event.target.value) }} required />
                            </Form.Group>
                            <Button variant="success" type="submit">Submit</Button>
                        </Form>
                    </Card.Body>
                </Card>
            </div>
        </main>
    )
}