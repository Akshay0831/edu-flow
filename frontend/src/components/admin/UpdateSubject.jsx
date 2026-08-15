import React, { useEffect, useReducer, useState } from "react";
import { toast } from "react-toastify";
import { useParams, useNavigate } from "react-router-dom";
import { Card, Form, Button, Modal, ButtonGroup } from "react-bootstrap";
import serverRequest from "../../helper/serverRequest";

export default function UpdateSubject() {

    const navigate = useNavigate();
    const { id } = useParams();
    const isUpdate = Boolean(id);
    document.title = (isUpdate ? "Update" : "Add") + " Subject";

    const defaultBatchMaxMarks = { IA1: { CO1: 18, CO2: 12 }, A1: { CO1: 6, CO2: 4 }, IA2: { CO2: 6, CO3: 18, CO4: 6 }, A2: { CO2: 2, CO3: 6, CO4: 2 }, IA3: { CO4: 12, CO5: 18 }, A3: { CO4: 4, CO5: 6 }, SEE: 60 };

    const reducer = (state, action) => {
        switch (action.type) {
            case "SET":
                return action.data;
            case "addBatch":
                return { ...state, [action.batch]: defaultBatchMaxMarks };
            case "updateTestValue":
                state[action.batch][action.test] = parseInt(action.value);
                return { ...state };
            case "updateCOnValue":
                state[action.batch][action.test][action.COn] = parseInt(action.value);
                return { ...state };
            case "deleteBatch":
                delete state[action.batch];
                return { ...state };
            case "deleteTest":
                delete state[action.batch][action.test];
                return { ...state };
            case "deleteCO":
                delete state[action.batch][action.test][action.COn];
                return { ...state };
            default:
                return state;
        }
    }

    const [departments, setDepartments] = useState([]);
    const [schemeCode, setSchemeCode] = useState("");
    const [subjectCode, setSubjectCode] = useState("");
    const [subjectName, setSubjectName] = useState("");
    const [maxMarks, dispatchMaxMarks] = useReducer(reducer, { [(new Date()).getFullYear()]: defaultBatchMaxMarks })
    const [semester, setSemester] = useState(1);
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
                const subjectsData = (await (await serverRequest("http://localhost:8000/documents/Subject")).json()).filter(doc => doc._id == id)[0];
                setSchemeCode(subjectsData["Scheme Code"]);
                setSubjectCode(subjectsData["Subject Code"]);
                setSubjectName(subjectsData["Subject Name"]);
                // setTestAssignmentRatio(subjectsData["Test Assignment Ratio"]);
                dispatchMaxMarks({ type: 'SET', data: subjectsData["Max Marks"] });
                setSemester(subjectsData["Semester"]);
                setDepartmentID(subjectsData["Department"]);
            }

            const departmentsData = await (await serverRequest("http://localhost:8000/documents/Department")).json();
            setDepartments(departmentsData);
        }
        fetchData();
    }, []);

    const onSubmitClicked = (event) => {
        event.preventDefault();
        let subject = {
            "Subject": {
                "Scheme Code": schemeCode,
                "Subject Code": subjectCode,
                "Subject Name": subjectName,
                "Max Marks": maxMarks,
                "Semester": semester,
                "Department": departmentId
            }
        };
        subject._id = id;

        serverRequest(`http://localhost:8000/Subject`, isUpdate ? "PUT" : "POST", subject)
            .then(async (res) => {
                if (!res.ok)
                    throw new Error(await res.json());
                navigate("/admin/collectionlist", { state: "Subject", });
                toasts(`${(isUpdate ? "Updated" : "Added")} Subject`, toast.success);
            }).catch(err => toasts(err.message, toast.error));
    }

    const [addModal, setAddModal] = useState(false);
    const [addModalBuffer, setAddModalBuffer] = useState("");

    const handleClose = () => setAddModal(false);

    const addToMaxMarksObject = () => {
        if (addModal[0]) {
            if (/^((IA|A|CO)[0-9]+|CIE|SEE)$/.test(addModalBuffer)) {
                if (addModal[1] && addModalBuffer.startsWith("CO")) maxMarks[addModal[0]][addModal[1]][addModalBuffer] = 0;
                else if (["SEE", "CIE"].includes(addModalBuffer)) {
                    if (addModalBuffer in maxMarks[addModal[0]]) toasts(addModalBuffer + " already present in Max Marks", toast.error);
                    else maxMarks[addModal[0]][addModalBuffer] = 60;
                }
                else if (!Object.keys(maxMarks).includes(addModalBuffer)) maxMarks[addModal[0]][addModalBuffer] = {};
            }
            else
                toasts("Invalid Format: " + addModalBuffer, toast.error);
        }
        else dispatchMaxMarks({ type: 'addBatch', batch: parseInt(addModalBuffer) });
        handleClose();
    };

    return (
        <main className="pt-5">
            <div className="container">
                <Modal show={addModal} onHide={handleClose}>
                    <Modal.Header closeButton>
                        <Modal.Title>Add Field</Modal.Title>
                    </Modal.Header>
                    <Modal.Body>Enter the field Name {addModal.length ? addModal.join("/") : ""}
                        <Form.Control type={addModal.length ? "text" : "number"} onChange={e => setAddModalBuffer(e.target.value.toUpperCase())} />
                    </Modal.Body>
                    <Modal.Footer>
                        <ButtonGroup>
                            <Button variant="secondary" onClick={handleClose}>
                                <i className="fa fa-close" />
                            </Button>
                            <Button variant="primary" onClick={addToMaxMarksObject}>
                                <i className="fa fa-plus" />
                            </Button>
                        </ButtonGroup>
                    </Modal.Footer>
                </Modal>
                <Card>
                    <Card.Header className="fs-3">{isUpdate ? "Update" : "Add"} Subject</Card.Header>
                    <Card.Body>
                        <Form onSubmit={onSubmitClicked}>
                            <Form.Group className="mb-3">
                                <Form.Label>Scheme Code:</Form.Label>
                                <Form.Control type="text" name="schemeCode" id="schemeCode" value={schemeCode} placeholder={"Enter Scheme Code"} onChange={(event) => { setSchemeCode(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Subject Code:</Form.Label>
                                <Form.Control type="text" name="subjectCode" id="subjectCode" value={subjectCode} placeholder={"Enter Subject Code"} onChange={(event) => { setSubjectCode(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Subject Name:</Form.Label>
                                <Form.Control type="text" name="subjectName" id="subjectName" value={subjectName} placeholder={"Enter Subject Name"} onChange={(event) => { setSubjectName(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="m-0 p-0 border rounded bg-light">
                                <Form.Label className="p-1"> Max Marks:</Form.Label><br />
                                {(Object.keys(maxMarks).map(batch =>
                                    <Card key={batch} className="ps-2">{batch}
                                        <Card.Body className="row p-0">
                                            {Object.keys(maxMarks[batch]).map(test => {
                                                if (typeof maxMarks[batch][test] === 'object') {
                                                    return <Card key={test} className="ps-2">{test}
                                                        <Card.Body className="row">
                                                            {Object.keys(maxMarks[batch][test]).map(CO => {
                                                                return <Form.Group key={CO} className="col"><Form.Label>{CO}</Form.Label><Form.Control type="number" placeholder={CO} value={maxMarks[batch][test][CO]} min="0" onChange={(e) => dispatchMaxMarks({ type: 'updateCOnValue', batch: batch, test: test, COn: CO, value: e.target.value })} /></Form.Group>
                                                            })}
                                                        </Card.Body>
                                                        <ButtonGroup className="col-2 mb-2">
                                                            <Button variant="outline-success" onClick={() => setAddModal([batch, test])} size="sm"><i className="fa fa-plus" /></Button>
                                                            <Button variant="outline-danger" onClick={() => dispatchMaxMarks({ type: "deleteTest", batch: batch, test: test })} size="sm"><i className="fa fa-trash" /></Button>
                                                        </ButtonGroup>
                                                    </Card>
                                                }
                                                else return <Card key={test} className="ps-2">
                                                    {test}
                                                    <Card.Body>
                                                        <Form.Control type="number" placeholder={test} value={maxMarks[batch][test]} min="0" onChange={(e) => dispatchMaxMarks({ type: 'updateTestValue', batch: batch, test: test, value: e.target.value })} />
                                                    </Card.Body>
                                                    <Button className="col-1 mb-2" variant="outline-danger" onClick={() => dispatchMaxMarks({ type: "deleteTest", batch: batch, test: test })} size="sm"><i className="fa fa-trash" /></Button>
                                                </Card>
                                            })}
                                        </Card.Body>

                                        <ButtonGroup size="sm" className="col-3 mb-2">
                                            <Button variant="outline-success" onClick={() => setAddModal([batch])}><i className="fa fa-plus" /></Button>
                                            <Button variant="outline-danger" onClick={() => dispatchMaxMarks({ type: "deleteBatch", batch: batch })}><i className="fa fa-trash" /></Button>
                                        </ButtonGroup>
                                    </Card>
                                ))}
                                <Button variant="outline-success" className="col-2 ms-2 mb-2" size="sm" onClick={() => setAddModal([])}><i className="fa fa-plus" /></Button>
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Semester:</Form.Label>
                                <Form.Control type="number" name="semester" id="semester" value={semester} placeholder={"Enter Semester"} onChange={(event) => { setSemester(event.target.value) }} required />
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
        </main >
    )
}