import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useNavigate, useParams } from "react-router-dom";
import { Card, Form, Button } from "react-bootstrap";
import serverRequest from "../../helper/serverRequest";

export default function UpdateCOPOMap() {

    const navigate = useNavigate();
    const { id } = useParams();
    const isUpdate = Boolean(id);
    document.title = (isUpdate ? "Update" : "Add") + " CO-PO Map";

    const [subjects, setSubjects] = useState([]);
    const [subjectId, setSubjectID] = useState("");
    const [CO, setCO] = useState("");
    const [PO, setPO] = useState("");
    const [val, setValue] = useState(0);

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
                const COPOMapData = (await (await serverRequest("http://localhost:8000/documents/CO PO Map")).json()).filter(doc => doc._id == id)[0];
                console.log(COPOMapData);
                setSubjectID(COPOMapData["Subject"]);
                setCO(COPOMapData["CO"]);
                setPO(COPOMapData["PO"]);
                setValue(COPOMapData["Value"]);
            }

            const subjectsData = await (await serverRequest("http://localhost:8000/documents/Subject")).json();
            setSubjects(subjectsData);
        }
        fetchData();
    }, []);

    const onSubmitClicked = (event) => {
        event.preventDefault();
        let copoMap = {
            "CO PO Map": {
                "Subject": subjectId,
                "CO": CO,
                "PO": PO,
                "Value": val,
            }
        }
        serverRequest(`http://localhost:8000/CO PO Map`, isUpdate ? "PUT" : "POST", copoMap, { "Content-Type": "application/json; charset=UTF-8" })
            .then(async (res) => {
                if (!res.ok)
                    throw new Error(await res.json());
                navigate("/admin/collectionlist", { state: "CO PO Map", });
                toasts(`${(isUpdate ? "Updated" : "Added")} CO PO Map`, toast.success);
            }).catch(err => toasts(err.message, toast.error));
    }

    const handleSubjectChange = (event) => setSubjectID(event.target.value);

    return (
        <main className="pt-5">
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">{isUpdate ? "Update" : "Add"} CO PO Map</Card.Header>
                    <Card.Body>
                        <Form onSubmit={onSubmitClicked}>
                            <Form.Group className="mb-3">
                                <Form.Label>Subject: </Form.Label>
                                <Form.Select name="department" value={subjectId} onChange={handleSubjectChange} required>
                                    <option value="">Select Subject</option>
                                    {subjects.map((subj) => {
                                        return <option key={subj._id} value={subj._id}>{subj["Subject Name"] + " (" + subj["Subject Code"] + ")"}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Course Outcome:</Form.Label>
                                <Form.Control type="text" name="CO" id="CO" value={CO} placeholder={"Course Outcome in format COn"} onChange={(event) => { setCO(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Program Outcome:</Form.Label>
                                <Form.Control type="text" name="PO" id="PO" value={PO} placeholder={"Program Outcome in format POn"} onChange={(event) => { setPO(event.target.value) }} required />
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Value:</Form.Label>
                                <Form.Control type="number" name="value" id="value" value={val} placeholder={"Value"} min="0" max="3" onChange={(event) => { setValue(parseInt(event.target.value)) }} required />
                            </Form.Group>
                            <Button variant="success" type="submit">Submit</Button>
                        </Form>
                    </Card.Body>
                </Card>
            </div>
        </main>
    )
}