import React, { useState, useEffect } from 'react';
import { toast } from "react-toastify";
import { InfinitySpin } from 'react-loader-spinner'
import { Card, Form } from 'react-bootstrap';
import BarGraph from './BarGraph';
import serverRequest from '../helper/serverRequest';

export default function AnalyticsOfStudent(props) {

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

    const subject = props.subject;
    const department = props.department;
    const [students, setStudents] = useState([]);
    const [studentID, setStudentID] = useState("");

    const [studentAnalyticsData, setStudentAnalyticsData] = useState(null);

    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        let fetchData = async () => {
            let studentsJSON = await (await serverRequest("http://localhost:8000/documents/Student")).json();
            if (department)
                studentsJSON = studentsJSON.filter(doc => doc.Department == department);
            setStudents(studentsJSON);
        }
        fetchData();
    }, []);

    let handleStudentSubmit = async (event) => {
        event.preventDefault();
        if (studentID.length) {
            setIsLoading(true);
            let data = await (await serverRequest(`http://localhost:8000/Analytics/predict_SEE_marks?Subject=${subject}&Student=${studentID}`)).json();
            let IALabels = [];
            let IAGraphData = [];
            let SEE = data.Marks["Marks Gained"].SEE;
            let predictedSEE = data.Predicted_SEE;
            let studentName = data.Student["Student Name"];
            delete data.Marks["Marks Gained"].SEE;

            let SumForIA = 0;
            let COsMarks = {};
            const marksGained = data.Marks["Marks Gained"];
            Object.keys(marksGained).forEach((ia) => {
                SumForIA += Object.values(marksGained[ia]).reduce((acc, cur) => acc + Number(cur), 0);

                for (const co in marksGained[ia])
                    COsMarks[co] = (COsMarks[co] || 0) + marksGained[ia][co];

                if (ia.startsWith("A")) {
                    IAGraphData.push(SumForIA);
                    SumForIA = 0;
                } else {
                    IALabels.push(ia);
                }
            })

            data.Marks["Marks Gained"].SEE = SEE;
            setStudentAnalyticsData({
                title: studentName + "'s internal performance",
                IALabels,
                IAGraphData,
                COGraphData: Object.values(COsMarks),
                COLabels: Object.keys(COsMarks),
                Student: data.Student,
                Marks: data.Marks,
                predictedSEE
            });

            setIsLoading(false);
        } else {
            setStudentAnalyticsData(null);
            toasts("Couldn't fetch the student", toast.error);
        }
    }

    return (
        <Card className='m-3'>
            {!isLoading
                ? <><Form onSubmit={handleStudentSubmit} className='m-3 px-2'>
                    <Form.Group className='row'>
                        <Form.Label className='col-md-3'>Select Student:</Form.Label>
                        <Form.Select className='col' value={studentID} onChange={(e) => setStudentID(e.target.value)} required>
                            <option value="">Select Student</option>
                            {students.map(stu => (<option key={stu._id} value={stu._id}>{stu.USN}</option>))}
                        </Form.Select>
                        <button type="submit" className='btn btn-success col-sm-2'>Submit</button>
                    </Form.Group>
                </Form>
                    {(studentAnalyticsData) ?
                        <div className='row p-3 gap-3'>
                            <div className="col-12 col-lg-7">
                                <BarGraph graphData={studentAnalyticsData.IAGraphData} labels={studentAnalyticsData.IALabels} title={studentAnalyticsData.title} />
                            </div>
                            <div className="col-12 col-lg-4">
                                <Card>
                                    <Card.Body>
                                        <Card.Title>{studentAnalyticsData.Student["Student Name"]}</Card.Title>
                                        <Card.Subtitle className="mb-2 text-muted">{studentAnalyticsData.Student.USN}</Card.Subtitle>
                                        <hr />
                                        <div className="d-flex flex-row align-items-center">
                                            <div className="flex-grow-1">
                                                <p>Semester Examination Marks:</p>
                                            </div>
                                            <div className="flex-grow-1" style={{ color: (studentAnalyticsData.predictedSEE > studentAnalyticsData.Marks["Marks Gained"].SEE) ? "red" : "green" }}>
                                                <p className='fs-3'>{studentAnalyticsData.Marks["Marks Gained"].SEE}</p>
                                            </div>
                                        </div>
                                        <div className="d-flex flex-row align-items-center">
                                            <div className="flex-grow-1">
                                                <p>Prediction Examination Marks:</p>
                                            </div>
                                            <div className="flex-grow-1">
                                                <p className='fs-3'>{studentAnalyticsData.predictedSEE}</p>
                                            </div>
                                        </div>
                                    </Card.Body>
                                </Card>
                            </div>
                            <div className="col-12">
                                <BarGraph graphData={studentAnalyticsData.COGraphData} labels={studentAnalyticsData.COLabels} title={studentAnalyticsData.title} />
                            </div>
                        </div> : null}</>
                : <div className='d-flex justify-content-center'><InfinitySpin color="#000" width='200' visible={true} /></div>}
        </Card>
    );
}