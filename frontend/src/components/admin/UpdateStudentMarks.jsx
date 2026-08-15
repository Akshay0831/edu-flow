import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useNavigate, useParams } from "react-router-dom";
import { Card, Form, Button } from "react-bootstrap";
import serverRequest from "../../helper/serverRequest";

export default function UpdateStudentMarks() {

    const navigate = useNavigate();
    const { id } = useParams();
    const isUpdate = Boolean(id);
    document.title = (isUpdate ? "Update" : "Add") + " Marks";

    const [subjects, setSubjects] = useState([]);
    const [subjectID, setSubjectID] = useState("");
    const [maxMarks, setMaxMarks] = useState({});
    const [students, setStudents] = useState([]);
    const [studentID, setStudentID] = useState("");
    const [marksGained, setMarksGained] = useState({ IA1: { CO1: 18, CO2: 12 }, A1: { CO1: 18, CO2: 12 }, IA2: { CO2: 6, CO3: 12, CO4: 6 }, A2: { CO2: 6, CO3: 12, CO4: 6 }, IA3: { CO4: 12, CO5: 18 }, A3: { CO4: 12, CO5: 18 }, SEE: 60 });

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
            setStudents(await (await serverRequest("http://localhost:8000/documents/Student")).json());
            let subjectsData = await (await serverRequest("http://localhost:8000/documents/Subject")).json()
            setSubjects(subjectsData);

            if (isUpdate) {
                const marksData = (await (await serverRequest("http://localhost:8000/documents/Marks")).json()).filter(doc => doc._id == id)[0];
                setMarksGained(marksData["Marks Gained"]);
                setSubjectID(marksData["Subject"]);
                setStudentID(marksData["Student"]);
                setMaxMarks((subjectsData.filter(doc => (doc._id == marksData["Subject"]))[0])["Max Marks"]);
            }

        }
        fetchData();
    }, []);

    const onSubmitClicked = (event) => {
        event.preventDefault();
        let marks = {
            "Marks": {
                "Marks Gained": marksGained,
                "Subject": subjectID,
                "Student": studentID,
            }
        }
        if (isUpdate) marks.Marks._id = id;
        serverRequest(`http://localhost:8000/Marks`, isUpdate ? "PUT" : "POST", marks)
            .then(async (res) => {
                if (!res.ok)
                    throw new Error(await res.json());
                navigate("/admin/collectionlist", { state: "Marks", });
                toasts(`${(isUpdate ? "Updated" : "Added")} Marks`, toast.success);
            }).catch(err => toasts(err.message, toast.error));
    }

    const handleSEEChange = (col, event) => {
        let marks = {};
        marks[col] = parseInt(event.target.value);
        setMarksGained(marksGained => ({ ...marksGained, ...marks }));
    }

    const handleCOChange = (col, CO, event) => {
        let marks = marksGained;
        marks[col][CO] = parseInt(event.target.value);
        setMarksGained(marksGained => ({ ...marksGained, ...marks }));
    }

    return (
        <main className="pt-5">
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">{isUpdate ? "Update" : "Add"} Marks</Card.Header>
                    <Card.Body>
                        <Form onSubmit={onSubmitClicked}>
                            <Form.Group className="mb-3">
                                <Form.Label>Student: </Form.Label>
                                <Form.Select name="student" value={studentID} onChange={(event) => setStudentID(event.target.value)} required>
                                    <option value="">Select Student</option>
                                    {students.map((student) => {
                                        return <option key={student._id} value={student._id}>{`${student["Student Name"]} (${student["USN"]})`}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="mb-3">
                                <Form.Label>Subject: </Form.Label>
                                <Form.Select name="subject" value={subjectID} onChange={(event) => { setSubjectID(event.target.value); setMaxMarks((subjects.filter(doc => (doc._id == event.target.value))[0])["Max Marks"]); }} required>
                                    <option value="">Select Subject</option>
                                    {subjects.map((subj) => {
                                        return <option key={subj._id} value={subj._id}>{`${subj["Subject Name"]} (${subj["Subject Code"]})`}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="m-0 p-0 border rounded bg-light">
                                <Form.Label className="p-1"> Marks Gained:</Form.Label>
                                {maxMarks
                                    ?
                                    Object.keys(maxMarks).map(test => {
                                        if (typeof maxMarks[test] === 'object') {
                                            return <Card key={test} className="ps-2">{test}
                                                <Card.Body className="row">
                                                    {Object.keys(maxMarks[test]).map(CO => {
                                                        return <Form.Group key={CO} className="col"><Form.Label>{CO}</Form.Label><Form.Control type="number" placeholder={CO} value={marksGained[test][CO]} min="0" max={maxMarks[test][CO]} onChange={handleCOChange.bind(this, test, CO)} /></Form.Group>
                                                    })}
                                                </Card.Body>
                                            </Card>
                                        }
                                        else return <Card key={test} className="p-3"> {test} <Form.Control type="number" placeholder={test} value={marksGained[test]} min="0" max={maxMarks[test]} onChange={handleSEEChange.bind(this, test)} /></Card>
                                    })
                                    : <>Max Marks not defined</>
                                }
                            </Form.Group>
                            <Button variant="success" type="submit">Submit</Button>
                        </Form>
                    </Card.Body>
                </Card>
            </div>
        </main>
    )
}