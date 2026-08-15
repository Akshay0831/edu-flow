import React, { useState, useEffect } from "react";
import { toast } from "react-toastify";
import { useNavigate, useParams } from "react-router-dom";
import { Card, Form, Button } from "react-bootstrap";
import * as XLSX from 'xlsx';
import serverRequest from "../../helper/serverRequest";

export default function UpdateFeedback() {

    const navigate = useNavigate();
    const { id } = useParams();
    const isUpdate = Boolean(id);
    document.title = (isUpdate ? "Update" : "Add") + " Feedback";

    const [subjects, setSubjects] = useState([]);
    const [subjectID, setSubjectID] = useState("");
    const [fileData, setFileData] = useState(null);
    const [feedback, setFeedback] = useState({ CO1: 0, CO2: 0, CO3: 0, CO4: 0, CO5: 0 });

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
            let subjectsData = await (await serverRequest("http://localhost:8000/documents/Subject")).json()
            setSubjects(subjectsData);

            if (isUpdate) {
                const marksData = (await (await serverRequest("http://localhost:8000/documents/Feedback")).json()).filter(doc => doc._id == id)[0];
                setFeedback(marksData["values"]);
                setSubjectID(marksData["Subject"]);
            }

        }
        fetchData();
    }, []);

    const uploadFile = async (event) => {
        let file = event.target.files[0];
        const data = await file.arrayBuffer();
        setFileData(data);
    }

    function getIndirectAttainmentValues(workbook) {

        // Get the sheet containing the responses
        // const worksheet = workbook.Sheets['Form Responses 1'];
        const worksheet = workbook.Sheets[workbook.SheetNames[0]];

        // Define the ratings mapping
        const rateLookup = {
            "Excellent": 5,
            "Very Good": 4,
            "Good": 3,
            "Satisfactory": 2,
            "Poor": 1
        };

        // Define the question to CO mapping
        const questionToCoMapping = {
            "Q1": "CO1",
            "Q2": "CO2",
            "Q3": "CO3",
            "Q4": "CO4",
            "Q5": "CO5"
        };

        // Get the range of cells containing data
        const range = worksheet['!ref'];
        // Extract the last row number from the range
        const lastRow = parseInt(range.split(':')[1].substring(1));

        // Define the indirect attainment object
        let indirectAttainment = {
            "CO1": 0,
            "CO2": 0,
            "CO3": 0,
            "CO4": 0,
            "CO5": 0
        };

        // Iterate over the rows of the worksheet
        for (let i = 2; i <= lastRow; i++) {
            // Get the USN, Name, question number, and ratings from the row
            const usn = worksheet[`B${i}`].v;
            const name = worksheet[`C${i}`].v;
            const studentFeedbacks = [
                worksheet[`D${i}`].v,
                worksheet[`E${i}`].v,
                worksheet[`F${i}`].v,
                worksheet[`G${i}`].v,
                worksheet[`H${i}`].v,
            ];
            // Iterate over the questions and calculate the indirect attainment for each CO based on the ratings
            for (const questionNumber in questionToCoMapping) {
                const coNumber = questionToCoMapping[questionNumber];
                const ratingIndex = parseInt(questionNumber.substring(1)) - 1;
                const rating = studentFeedbacks[ratingIndex];

                // console.log(coNumber, rating, rateLookup, rateLookup[rating]);
                if (coNumber && rating && rateLookup[rating]) {
                    indirectAttainment[coNumber] += rateLookup[rating];
                }
            }
        }

        // Calculate the final indirect attainment for each CO
        for (const coNumber in indirectAttainment) {
            indirectAttainment[coNumber] = Math.round(indirectAttainment[coNumber] / (lastRow * 5) * 100);
        }

        // Print the indirect attainment object
        return indirectAttainment;
    }

    function addData() {
        if (!fileData) return;
        const workbook = XLSX.read(fileData);
        let indirectAttainment = getIndirectAttainmentValues(workbook);
        console.log("Indirected Attainment from XLSX input: ", indirectAttainment);
        setFeedback(indirectAttainment);
    }

    const onSubmitClicked = (event) => {
        event.preventDefault();
        let feedbackDoc = {
            "Feedback": {
                "values": feedback,
                "Subject": subjectID,
            }
        }
        if (isUpdate) feedbackDoc._id = id;

        serverRequest(`http://localhost:8000/Feedback`, isUpdate ? "PUT" : "POST", feedbackDoc, { "Content-Type": "application/json; charset=UTF-8" })
            .then(async (res) => {
                if (!res.ok)
                    throw new Error(await res.json());
                navigate("/admin/collectionlist", { state: "Feedback", });
                toasts(`${(isUpdate ? "Updated" : "Added")} Feedback`, toast.success);
            }).catch(err => toasts(err.message, toast.error));
    }

    return (
        <main className="pt-5">
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">{isUpdate ? "Update" : "Add"} Feedback</Card.Header>
                    <Card.Body>
                        <Form onSubmit={onSubmitClicked}>
                            <Form.Group className="mb-3">
                                <Form.Label>Subject: </Form.Label>
                                <Form.Select name="subject" value={subjectID} onChange={(event) => { setSubjectID(event.target.value); }} required>
                                    <option value="">Select Subject</option>
                                    {subjects.map((subj) => {
                                        return <option key={subj._id} value={subj._id}>{`${subj["Subject Name"]} (${subj["Subject Code"]})`}</option>
                                    })}
                                </Form.Select>
                            </Form.Group>
                            <Form.Group className="row border rounded m-0 mb-3 p-1">
                                <Form.Label className="p-0">XLSX Input (Optional): </Form.Label>
                                <Form.Control className="col" type="file" name="file" onChange={uploadFile} />
                                {fileData && <Button type="button" className="btn btn-primary col-md-1 col-sm-2" onClick={() => addData()}>
                                    <i className="fas fa-upload"></i>
                                </Button>}
                            </Form.Group>
                            <Form.Group className="mb-3 p-1 border rounded bg-light">
                                <Form.Label className="p-1 m-0"> Feedback Values:</Form.Label>
                                {
                                    Object.keys(feedback).map(co => {
                                        return <Card key={co}>
                                            <Card.Body className="py-1">
                                                <Form.Group className="row"><Form.Label>{co}</Form.Label><Form.Control type="number" placeholder={co} value={feedback[co]} min="0" max="100" onChange={() => setFeedback({ ...feedback, [co]: parseInt(event.target.value) })} /></Form.Group>
                                            </Card.Body>
                                        </Card>
                                    })
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