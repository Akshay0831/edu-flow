import React, { useState, useEffect } from 'react';
import { InfinitySpin } from 'react-loader-spinner';
import { Accordion, Button, Card, Form, Tab, Tabs } from 'react-bootstrap';
import { toast } from "react-toastify";
import serverRequest from '../helper/serverRequest';

document.title = "Report Generation";
export default function AccreditationReportGeneration(props) {
    function toasts(message, type) {
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
    };

    function criteria3ReportForm(props) {
        const defaultTargetValues = [50, 55, 60];
        const defaultMarksThreshold = 60;

        const [minA, setMinA] = useState(27);
        const [minT, setMinT] = useState(14);
        const [departments, setDepartments] = useState([]);
        const [departmentId, setDepartmentId] = useState("");
        const [originalSubjects, setOriginalSubjects] = useState([]);
        const [subjects, setSubjects] = useState([]);
        const [subjectId, setSubjectId] = useState("");
        const [marksThreshold, setMarksThreshold] = useState(defaultMarksThreshold)
        const [generatingReport, setGeneratingReport] = useState(false);
        const [numbers, setNumbers] = useState(defaultTargetValues);
        const [batch, setBatch] = useState(2018);

        useEffect(() => {
            let fetchData = async () => {
                setDepartments(await (await serverRequest("http://localhost:8000/documents/Department")).json());
                setOriginalSubjects(await (await serverRequest("http://localhost:8000/documents/Subject")).json());
            }
            fetchData();
        }, []);

        useEffect(() => {
            let fetchSubjectData = async () => {
                setSubjectId("");
                setSubjects(originalSubjects.filter(subject => subject.Department === departmentId));
            }
            fetchSubjectData();
        }, [departmentId]);

        const handleInputChange = (event) => {
            const { value } = event.target;
            const newNumbers = value.split(',')
                .map((number) => Number(number.trim()))
                .filter((number) => number >= 1 && number <= 100)
                .sort((a, b) => a - b);
            setNumbers(newNumbers);
        };

        const onGenerateReportClicked = async (event) => {
            event.preventDefault();
            setGeneratingReport(true);
            let options = {
                batch: batch,
                targetValues: numbers.length ? numbers : defaultTargetValues,
                marksThreshold: marksThreshold ? parseInt(marksThreshold) : defaultMarksThreshold,
            };
            if (subjectId) {
                let subject = subjects.find(sub => sub._id == subjectId);
                let response = await serverRequest("http://localhost:8000/reportGeneration/" + subjectId, "POST", options);
                const blob = await response.blob();
                const url = window.URL.createObjectURL(new Blob([blob]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', subject["Subject Code"] + ".xlsx");
                document.body.appendChild(link);
                link.click();
                setGeneratingReport(false);
            }
        }

        const GenerateGapAnalysisReport = async () => {
            setGeneratingReport(true);
            let options = {
                department: departmentId,
                batch: batch,
                A:minA,
                T:minT,
                targetValues: numbers.length ? numbers : defaultTargetValues,
                marksThreshold: marksThreshold ? parseInt(marksThreshold) : defaultMarksThreshold,
            };
            // console.log(options);
            try {
                let response = await serverRequest("http://localhost:8000/reportGeneration/gapAnalysis", "POST", options);
                const blob = await response.blob();
                const url = window.URL.createObjectURL(new Blob([blob]));
                const link = document.createElement('a');
                link.href = url;
                link.setAttribute('download', `${departments.find(dept => dept._id === departmentId)["Department Name"]} ${batch}.xlsx`);
                document.body.appendChild(link);
                link.click();
                // console.log(response);
                toasts("Generated Report", toast.success)
            }
            catch (err) {
                console.log(err);
                toasts(err.message, toast.error);
            }
            setGeneratingReport(false);
        }

        return generatingReport
            ? <>
                <div className='d-flex justify-content-center'>Generating Report...</div>
                <div className='d-flex justify-content-center'><InfinitySpin color="#000" width='200' visible={true} /></div>
            </>
            : <Tabs defaultActiveKey="gapAnalysis" className="mb-2">
                <Tab eventKey="gapAnalysis" title="Gap Analysis">
                    <Form onSubmit={onGenerateReportClicked} className='p-1'>
                        <Form.Group className='m-2'>
                            <Form.Label>Department: </Form.Label>
                            <Form.Select name="department" value={departmentId} required onChange={(e) => { setDepartmentId(e.target.value); }}>
                                <option value={""}>Open this select menu</option>
                                {departments.map(dept => {
                                    return <option key={dept._id} value={dept._id}>{dept["Department Name"]}</option>
                                })}
                            </Form.Select>
                        </Form.Group>
                        <Form.Group className='m-2'>
                            <Form.Label>Batch:</Form.Label>
                            <Form.Control type="number" min={2000} max={2099} placeholder="Enter batch" onChange={(e) => setBatch(e.target.value)} value={batch} />
                        </Form.Group>
                        <Accordion><Accordion.Item eventKey="0">
                            <Accordion.Header>Optional Fields</Accordion.Header>
                            <Accordion.Body className='p-1'>
                                <Form.Group className='m-2'>
                                    <Form.Label>A (Minimum SUM PO value needed):</Form.Label>
                                    <Form.Control type="number" min={1} max={99} placeholder="Enter the minimum PO value needed" onChange={(e) => setMinA(e.target.value)} value={minA} />
                                </Form.Group>
                                <Form.Group className='m-2'>
                                    <Form.Label>T (Minimum Number of PO attained subjects needed):</Form.Label>
                                    <Form.Control type="number" min={1} max={99} placeholder="Enter the minimum number of subjects addressing PO needed" onChange={(e) => setMinT(e.target.value)} value={minT} />
                                </Form.Group>
                                <Form.Group className='m-2'>
                                    <Form.Label>Marks Threshold:</Form.Label>
                                    <Form.Control type="number" min={1} max={99} placeholder="Enter minimum marks for CO attainment" onChange={(e) => setMarksThreshold(e.target.value)} value={marksThreshold} />
                                </Form.Group>
                                <Form.Group controlId="numberList" className='m-2'>
                                    <Form.Label>List of Target Levels:</Form.Label>
                                    <Form.Control type="text" placeholder="Enter numbers separated by commas" onChange={handleInputChange} defaultValue={numbers.join(', ')} />
                                    <Form.Text className="text-muted">Enter numbers between 1 and 100.</Form.Text>
                                </Form.Group>
                            </Accordion.Body>
                        </Accordion.Item></Accordion>
                        <Button variant='warning' className='m-2' onClick={GenerateGapAnalysisReport} disabled={!departmentId || !batch}>Generate Department Gap Analysis Report</Button>
                    </Form>
                </Tab>
                <Tab eventKey="subjectAttainment" title="Specific Subject Attainment">
                    <Form onSubmit={onGenerateReportClicked} className='p-1'>
                        <Form.Group className='m-2'>
                            <Form.Label>Department: </Form.Label>
                            <Form.Select name="department" value={departmentId} required onChange={(e) => { setDepartmentId(e.target.value); }}>
                                <option value="">Open this select menu</option>
                                {departments.map(dept => {
                                    return <option key={dept._id} value={dept._id}>{dept["Department Name"]}</option>
                                })}
                            </Form.Select>
                        </Form.Group>
                        <Form.Group className='m-2'>
                            <Form.Label>Subject: {departmentId ? null : <span className='text-danger'>Select Department First</span>}</Form.Label>
                            <Form.Select name="subject" disabled={!departmentId} value={subjectId} required onChange={(e) => { setSubjectId(e.target.value); }}>
                                <option value="">Open this select menu</option>
                                {subjects.map(subject => {
                                    return <option key={subject._id} value={subject._id}>{String(subject["Subject Name"] + " (" + subject["Subject Code"] + ")").toUpperCase()}</option>
                                })}
                            </Form.Select>
                        </Form.Group>
                        <Form.Group className='m-2'>
                            <Form.Label>Batch:</Form.Label>
                            <Form.Control type="number" min={2000} max={2099} placeholder="Enter batch" onChange={(e) => setBatch(e.target.value)} value={batch} />
                        </Form.Group>
                        <Accordion><Accordion.Item eventKey="0">
                            <Accordion.Header>Optional Fields</Accordion.Header>
                            <Accordion.Body className='p-1'>
                                <Form.Group className='m-2'>
                                    <Form.Label>Marks Threshold:</Form.Label>
                                    <Form.Control type="number" min={1} max={99} placeholder="Enter minimum marks for CO attainment" onChange={(e) => setMarksThreshold(e.target.value)} value={marksThreshold} />
                                </Form.Group>
                                <Form.Group controlId="numberList" className='m-2'>
                                    <Form.Label>List of Target Levels:</Form.Label>
                                    <Form.Control type="text" placeholder="Enter numbers separated by commas" onChange={handleInputChange} defaultValue={numbers.join(', ')} />
                                    <Form.Text className="text-muted">Enter numbers between 1 and 100.</Form.Text>
                                </Form.Group>
                            </Accordion.Body>
                        </Accordion.Item></Accordion>
                        <Button variant='success' className='m-2' type='submit' disabled={!subjectId || numbers.length === 0}>Generate Subject Attainment Report</Button>
                    </Form>
                </Tab>
            </Tabs>
    }

    return (
        <main className="pt-5" >
            <div className='container'>
                <Card>
                    <Card.Header className='fs-3'>Generate NBA Accreditation Reports</Card.Header>
                    <Card.Body>
                        <Accordion defaultActiveKey="3">
                            <Accordion.Item eventKey="1">
                                <Accordion.Header>CRITERION 1 : Vision, Mission and Program Educational Objectives (60)</Accordion.Header>
                                <Accordion.Body className='d-flex justify-content-center fs-4'>
                                    <i className="fa-solid fa-person-digging p-2" /> Work In Progress
                                </Accordion.Body>
                            </Accordion.Item>
                            <Accordion.Item eventKey="2">
                                <Accordion.Header>CRITERION 2 : Program Curriculum and Teaching – Learning Processes (120)</Accordion.Header>
                                <Accordion.Body className='d-flex justify-content-center fs-4'>
                                    <i className="fa-solid fa-person-digging p-2" /> Work In Progress
                                </Accordion.Body>
                            </Accordion.Item>
                            <Accordion.Item eventKey="3">
                                <Accordion.Header>CRITERION 3 : Course Outcomes and Program Outcomes (120)</Accordion.Header>
                                <Accordion.Body className='p-0'>
                                    {criteria3ReportForm(props)}
                                </Accordion.Body>
                            </Accordion.Item>
                            <Accordion.Item eventKey="4">
                                <Accordion.Header>CRITERION 4 : Students’ Performance (150)</Accordion.Header>
                                <Accordion.Body className='d-flex justify-content-center fs-4'>
                                    <i className="fa-solid fa-person-digging p-2" /> Work In Progress
                                </Accordion.Body>
                            </Accordion.Item>
                            <Accordion.Item eventKey="5">
                                <Accordion.Header>CRITERION 5 : Faculty Information and Contributions (200)</Accordion.Header>
                                <Accordion.Body className='d-flex justify-content-center fs-4'>
                                    <i className="fa-solid fa-person-digging p-2" /> Work In Progress
                                </Accordion.Body>
                            </Accordion.Item>
                            <Accordion.Item eventKey="6">
                                <Accordion.Header>CRITERION 6 : Facilities and Technical Support (80)</Accordion.Header>
                                <Accordion.Body className='d-flex justify-content-center fs-4'>
                                    <i className="fa-solid fa-person-digging p-2" /> Work In Progress
                                </Accordion.Body>
                            </Accordion.Item>
                            <Accordion.Item eventKey="7">
                                <Accordion.Header>CRITERION 7 : Continuous Improvement (50)</Accordion.Header>
                                <Accordion.Body className='d-flex justify-content-center fs-4'>
                                    <i className="fa-solid fa-person-digging p-2" /> Work In Progress
                                </Accordion.Body>
                            </Accordion.Item>
                        </Accordion>
                    </Card.Body>
                </Card>
            </div>
        </main>
    );
}
