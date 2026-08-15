import React, { useContext, useEffect, useState } from 'react';
import { Accordion, Button, Card, Form, Table } from "react-bootstrap";
import { toast } from "react-toastify";
import { InfinitySpin } from 'react-loader-spinner';
import BatchInput from "./BatchInput";
import serverRequest from '../../helper/serverRequest';
import { AuthContext } from "../AuthContext";

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

function deepCopyObject(originalObject, defaultValue = null) {
    const copiedObject = {};
    for (let key in originalObject) {
        if (typeof originalObject[key] === 'object')
            copiedObject[key] = deepCopyObject(originalObject[key], defaultValue);
        else if (defaultValue != null)
            copiedObject[key] = defaultValue;
        else
            copiedObject[key] = originalObject[key];
    }
    return copiedObject;
}

export default function TeacherUpdateMarksTable(props) {
    const serverURL = 'http://localhost:8000/';
    document.title = "Update Marks Table";

    const { user } = useContext(AuthContext);
    const userType = user.userType;
    const userMail = user.userMail;

    if (!user) return;

    const [batch, setBatch] = useState(2018);
    const [batches, setBatches] = useState([]);
    const [subjects, setSubjects] = useState([]);
    const [subjectSelected, setSubjectSelected] = useState({});
    const [marksTable, setMarksTable] = useState([]);

    useEffect(() => {
        const fetchSubjects = async () => {
            if (userType == "Teacher")
                setSubjects(await (await serverRequest(serverURL + 'subjectsTaught/' + userMail)).json());
            else if (userType == "Admin")
                setSubjects(await (await serverRequest(serverURL + 'documents/Subject')).json());
        }
        fetchSubjects();
    }, []);

    useEffect(() => {
        if (subjectSelected["Max Marks"]) {
            let batchesList = Object.keys(subjectSelected["Max Marks"]);
            setBatches(batchesList);
            setBatch(batchesList.at(0));
        }
    }, [subjectSelected]);

    useEffect(() => {
        const fetchData = async () => {
            if (subjectSelected["Max Marks"] && batch) {
                let marksData = await (await serverRequest(`${serverURL}Marks/table?teacherMail=${userMail}&subjectID=${subjectSelected._id}`)).json();
                setMarksTable(marksData)
            }
        }
        fetchData();
    }, [subjectSelected, batch]);

    function totalIA(IAObj) {
        let sum = 0;
        if (IAObj)
            Object.keys(IAObj).forEach(co => { sum += Number(IAObj[co]) });
        return sum;
    }

    function inputValidation(inputMarks, maxMarksObj, ia, co) {
        if (inputMarks <= maxMarksObj[ia][co]) {
            if (inputMarks >= 0) {
                return Number(inputMarks);
            }
            toasts("Marks value must be greater than or equal to 0", toast.error)
            return 0;
        }
        toasts("Marks value must be less than or equal to " + maxMarksObj[ia][co], toast.error)
        return Number(maxMarksObj[ia][co]);
    }

    function handleItemChanged(classIndex, studentIndex, ia, co, event) {
        let marks = [...marksTable];
        if (!marks[classIndex].Class.Students[studentIndex].Marks.length) {
            marks[classIndex].Class.Students[studentIndex].Marks = { "Subject": subjectSelected._id, "Student": marks[classIndex].Class.Students[studentIndex]._id, "Marks Gained": deepCopyObject(subjectSelected["Max Marks"][batch], 0) };
        }
        if (!["SEE", "CIE"].includes(ia)) {
            marks[classIndex].Class.Students[studentIndex].Marks["Marks Gained"][ia][co] = inputValidation(event.target.value, subjectSelected["Max Marks"][batch], ia, co);
        } else {
            marks[classIndex].Class.Students[studentIndex].Marks["Marks Gained"][ia] = Number(event.target.value);
        }
        setMarksTable(marks);
    }

    function updateDocument(marksObj) {
        serverRequest((marksObj._id ? ("http://localhost:8000/documents/Marks/update/" + marksObj._id) : "http://localhost:8000/documents/Marks/add"), "POST", marksObj)
            .then((res) => {
                if (res.status == 200) {
                    this.toasts("Updated Successfully!", toast.success);
                }
            });
    }

    return (
        <main className="pt-5" >
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">Update Marks</Card.Header>
                    <Card.Body>
                        <Form.Group className="mb-3">
                            <Form.Label>Subject:</Form.Label>
                            <Form.Select value={JSON.stringify(subjectSelected)} name="subjectSelected" onChange={(e) => setSubjectSelected(JSON.parse(e.target.value))} required>
                                <option value={{}}>Select Subject</option>
                                {subjects &&
                                    subjects.map(sub => <option key={sub._id} value={JSON.stringify(sub)}>{sub["Subject Name"]} ({sub["Subject Code"]})</option>)}
                            </Form.Select>
                        </Form.Group>
                        <Form.Group className="mb-3">
                            <Form.Label>Batch:</Form.Label>
                            <Form.Select value={batch} name="batch" onChange={(e) => setBatch(e.target.value)} required>
                                <option value="">Select Batch</option>
                                {batches &&
                                    batches.map(batch => <option key={batch}> {batch} </option>)}
                            </Form.Select>
                        </Form.Group>
                        {marksTable &&
                            <Accordion defaultActiveKey="0">
                                {marksTable.map((classObj, classIndex) => (
                                    <Accordion.Item key={classIndex} eventKey={classIndex}>
                                        <Accordion.Header>{classObj.Class["Semester"] + classObj.Class["Section"]}</Accordion.Header>
                                        <Accordion.Body>
                                            <BatchInput batch={batch} deptId={subjectSelected.Department} classId={classObj.Class._id} subjectId={subjectSelected._id} subjectCode={subjectSelected["Subject Code"]} />
                                            <div className='overflow-auto table-responsive'>
                                                <Table striped hover bordered style={{ fontSize: "15px" }}>
                                                    <thead>
                                                        <tr>
                                                            <th scope="col" className="text-center" rowSpan="2">Sl. No</th>
                                                            <th scope="col" className="text-center" rowSpan="2">USN</th>
                                                            <th scope="col" className="text-center" rowSpan="2">Name</th>
                                                            {Object.keys(subjectSelected["Max Marks"][batch]).map(i => {
                                                                return (
                                                                    <th
                                                                        colSpan={Object.keys(subjectSelected["Max Marks"][batch][i]).length + 1}
                                                                        rowSpan={["SEE", "CIE"].includes(i) ? 2 : 1}
                                                                        scope="col"
                                                                        className="text-center"
                                                                        key={i}>
                                                                        {i}
                                                                    </th>
                                                                )
                                                            })}
                                                            <th scope="col" className="text-center" rowSpan="2">...</th>
                                                        </tr>
                                                        <tr>
                                                            {Object.keys(subjectSelected["Max Marks"][batch]).filter(obj => !["SEE", "CIE"].includes(obj)).map((ia, i) => {
                                                                return ([Object.keys(subjectSelected["Max Marks"][batch][ia]).map((co, c) => {
                                                                    return (
                                                                        <th scope="col" className="text-center" key={ia + co}>{co}</th>
                                                                    );
                                                                }), <th scope="col" className="text-center" key={i}>Total</th>])
                                                            })}
                                                        </tr>
                                                    </thead>
                                                    <tbody>
                                                        {classObj.Class.Students.map((student, studentIndex) => (
                                                            <tr key={studentIndex}>
                                                                <td>{studentIndex + 1}</td>
                                                                <td>{student.USN}</td>
                                                                <td>{student["Student Name"]}</td>
                                                                {Object.keys(subjectSelected["Max Marks"][batch]).map(ia => (
                                                                    [Object.keys(subjectSelected["Max Marks"][batch][ia]).map(co => {
                                                                        if (!["SEE", "CIE"].includes(ia)) {
                                                                            return (
                                                                                <td key={ia + co} style={{ minWidth: "100px" }} className='p-1'>
                                                                                    <Form.Control type="number" min="0" max={subjectSelected["Max Marks"][batch][ia][co]}
                                                                                        placeholder={(student.Marks["Marks Gained"] && Object.keys(student.Marks["Marks Gained"]).length ? (student.Marks["Marks Gained"][ia][co]) : "0") + "/" + subjectSelected["Max Marks"][batch][ia][co]}
                                                                                        onChange={handleItemChanged.bind(this, classIndex, studentIndex, ia, co)} />
                                                                                </td>
                                                                            )
                                                                        }
                                                                    }), (!["SEE", "CIE"].includes(ia))
                                                                        ? <td key={"total_" + ia}>{totalIA((student.Marks["Marks Gained"] ? student.Marks["Marks Gained"][ia] : 0)) + "/" + totalIA(subjectSelected["Max Marks"][batch][ia])}</td>
                                                                        : (
                                                                            <td key={ia} style={{ minWidth: "100px" }}>
                                                                                <Form.Control type="number" min="0" max={subjectSelected["Max Marks"][batch][ia]}
                                                                                    placeholder={(student.Marks["Marks Gained"] ? student.Marks["Marks Gained"][ia] : "0") + "/" + subjectSelected["Max Marks"][batch][ia]}
                                                                                    onChange={handleItemChanged.bind(this, classIndex, studentIndex, ia, null)} />
                                                                            </td>
                                                                        )]

                                                                ))}
                                                                <td>
                                                                    <Button variant="warning" className="py-1" onClick={() => updateDocument(student.Marks)}>
                                                                        <i className="fa fa-pencil" aria-hidden="true" />
                                                                    </Button>
                                                                </td>
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </Table>
                                            </div>
                                        </Accordion.Body>
                                    </Accordion.Item>
                                ))}
                            </Accordion>
                        }
                    </Card.Body>
                </Card>
                <Card className="table-responsive p-3">
                    <Table bordered className="p-0">
                        <thead>
                            <tr>
                                <th>Abbreviation</th>
                                <th>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>IA</td>
                                <td>Internal Assessment</td>
                            </tr>
                            <tr>
                                <td>A</td>
                                <td>Assignment</td>
                            </tr>
                            <tr>
                                <td>CO</td>
                                <td>Course Outcome</td>
                            </tr>
                            <tr>
                                <td>CIE</td>
                                <td>Continuous Internal Evaluation</td>
                            </tr>
                            <tr>
                                <td>SEE</td>
                                <td>Semester End Examination</td>
                            </tr>
                        </tbody>
                    </Table>
                </Card>
            </div>
        </main>
    );
}