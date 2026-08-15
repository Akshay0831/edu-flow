import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useNavigate, useParams } from "react-router-dom";
import { Card, Form, Button } from "react-bootstrap";
import serverRequest from "../../helper/serverRequest";

export default function UpdateDepartment() {

    const navigate = useNavigate();
    const { id } = useParams();
    const isUpdate = Boolean(id);
    document.title = (isUpdate ? "Update" : "Add") + " Department";

    const [teachers, setTeachers] = useState([]);
    const [name, setName] = useState("");
    const [hod, setHOD] = useState("");

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
                const departmentData = (await (await serverRequest("http://localhost:8000/documents/Department")).json()).filter(doc => doc._id == id)[0];
                console.log(departmentData);
                setName(departmentData["Department Name"]);
                setHOD(departmentData["HoD"]);
            }

            const teachersData = await (await serverRequest("http://localhost:8000/documents/Teacher")).json();
            setTeachers(teachersData);
        }
        fetchData();
    }, []);

    const onSubmitClicked = (event) => {
        event.preventDefault();
        let department = {
            "Department": {
                "Department Name": name,
                "HoD": hod,
            }
        }
        if (isUpdate) department._id = id;
        serverRequest(`http://localhost:8000/Department`, isUpdate ? "PUT" : "POST", department, { "Content-Type": "application/json; charset=UTF-8" })
            .then(async (res) => {
                if (!res.ok)
                    throw new Error(await res.json());
                navigate("/admin/collectionlist", { state: "Department", });
                toasts(`${(isUpdate ? "Updated" : "Added")} Department`, toast.success);
            }).catch(err => toasts(err.message, toast.error));
    }

    const handleHODChange = (event) => setHOD(event.target.value);

    return (
        <main className="pt-5">
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">{isUpdate ? "Update" : "Add"} Department</Card.Header>
                    <Card.Body>
                        <Form onSubmit={onSubmitClicked}>
                            <Form.Group className="mb-3">
                                <Form.Label>Department Name:</Form.Label>
                                <Form.Control type="text" name="name" id="name" value={name} placeholder={"Department Name"} onChange={(event) => { setName(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Head of Department: </Form.Label>
                                <Form.Select name="department" value={hod} onChange={handleHODChange}>
                                    <option value="">Select HOD from teachers</option>
                                    {teachers.map((teacher) => {
                                        return <option key={teacher._id} value={teacher._id}>{teacher["Teacher Name"] + " (" + teacher["Mail"] + ")"}</option>
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