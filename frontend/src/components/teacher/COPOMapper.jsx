import React, { useContext, useEffect, useState } from "react";
import { toast } from "react-toastify";
import { Card, Table } from "react-bootstrap";
import serverRequest from "../../helper/serverRequest";
import { AuthContext } from "../AuthContext";

export default function COPOMapper() {

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

    const serverURL = 'http://localhost:8000/';
    document.title = "CO PO Mapper";

    const { user } = useContext(AuthContext);
    const userType = user.userType;
    const userMail = user.userMail;

    const [batch, setBatch] = useState(2018);
    const [batches, setBatches] = useState([]);
    const [subjectSelected, setSubjectSelected] = useState("");
    const [subjects, setSubjects] = useState([]);
    const [COPOCollection, setCOPOCollection] = useState([]);
    const [COPOMaps, setCOPOMaps] = useState([[], []]);
    const [COs, setCOs] = useState(['CO1', 'CO2', 'CO3', 'CO4', 'CO5']);
    let POs = ['PO1', 'PO2', 'PO3', 'PO4', 'PO5', 'PO6', 'PO7', 'PO8', 'PO9', 'PO10', 'PO11', 'PO12', 'PSO1', 'PSO2'];

    useEffect(() => {
        const fetchData = async () => {
            console.log("Called API to fetch subjects and COPO Collection");
            setCOPOCollection(await (await serverRequest(serverURL + 'documents/CO PO Map')).json());
            if (userType == "Teacher")
                setSubjects(await (await serverRequest(serverURL + 'subjectsTaught/' + userMail)).json());
            else if (userType == "Admin")
                setSubjects(await (await serverRequest(serverURL + 'documents/Subject')).json());
        }
        fetchData();
    }, []);

    function getCOsFromMaxMarks(maxMarks) {
        let cos = []
        for (let ia in maxMarks)
            if (typeof maxMarks[ia] == "object")
                for (let co in maxMarks[ia])
                    if (!cos.includes(co))
                        cos.push(co);
        return cos;
    }

    useEffect(() => {
        let COPOMap = {}
        for (let CO of COs) {
            let POObjs = {};
            for (let PO of POs)
                POObjs[PO] = "";
            COPOMap[CO] = POObjs;
        }
        for (let doc of COPOCollection)
            if (doc.Subject == subjectSelected)
                COPOMap[doc.CO][doc.PO] = doc.Value;
        setCOPOMaps(COPOMap);
    }, [COs]);

    useEffect(() => {
        if (subjectSelected && batch) {
            let cos = getCOsFromMaxMarks(subjects.find(doc => doc._id == subjectSelected)["Max Marks"][batch]);
            setCOs(cos);
        }
    }, [subjectSelected, batch]);

    useEffect(() => {
        if (subjectSelected) {
            let batchesList = Object.keys(subjects.find(doc => doc._id == subjectSelected)["Max Marks"]);
            setBatches(batchesList);
            setBatch(batchesList.at(0));
        }
    }, [subjectSelected]);


    const updateCOPOMapping = () => {
        if (subjectSelected)
            serverRequest(serverURL + 'CO PO Map/table/' + subjectSelected, "POST", COPOMaps)
                .then(res => {
                    if (res.status == 200) {
                        console.log("Updated CO-PO Mapping for " + subjectSelected + " Successfully!");
                        toasts("Updated CO-PO Mapping Successfully!", toast.success);
                    }
                })
                .catch(err => {
                    console.error(err);
                    toasts("Error: " + err.message, toast.error);
                });
        else toasts("Please Select the Subject First", toast.error);
        serverRequest(serverURL + 'documents/CO PO Map').then(docs => docs.json()).then(docs => setCOPOCollection(docs));
    }

    return (
        <main className="pt-5">
            <div className="container">
                <Card>
                    <Card.Header className="fs-3">CO PO Mapper</Card.Header>
                    {
                        subjects.length
                            ? <Card.Body className="overflow-auto">
                                <select className="form-select mb-3" value={subjectSelected} aria-label="Select Subject" onChange={() => setSubjectSelected(event.target.value)}>
                                    <option value="">Select Subject</option>
                                    {subjects
                                        ? subjects.map(sub => {
                                            return <option key={sub._id} value={sub._id}>
                                                {sub["Subject Name"]} ({sub["Subject Code"]})
                                            </option>
                                        })
                                        : ""}
                                </select>
                                <select className="form-select mb-3" value={batch} aria-label="Select Batch" onChange={(e) => setBatch(e.target.value)}>
                                    <option value="">Select Batch</option>
                                    {batches
                                        ? batches.map(batch => {
                                            return <option key={batch}> {batch} </option>
                                        })
                                        : ""}
                                </select>
                                {COPOMaps
                                    ? <Table striped bordered hover size="sm">
                                        <thead className="thead-light">
                                            <tr>
                                                <th></th>
                                                {COs.map(COn => <th key={COn}>{COn}</th>)}
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {POs.map(POn => {
                                                return <tr key={POn}>
                                                    <th>{POn}</th>
                                                    {COs.map(COn => {
                                                        return <td key={COn}>
                                                            {COPOMaps[COn] && <input type="number" min="0" max="3" className="bg-transparent border-0 w-100" placeholder={COn + "/" + POn} value={COPOMaps[COn][POn]} onChange={(e) => setCOPOMaps(COPOMap => ({ ...COPOMap, [COn]: { ...COPOMap[COn], [POn]: e.target.value } }))} />}
                                                        </td>
                                                    })}
                                                </tr>
                                            })}
                                        </tbody>
                                    </Table>
                                    : <p>No Values Found</p>}
                                <button className="btn btn-success" onClick={() => updateCOPOMapping()}>Save&nbsp; Changes</button>
                            </Card.Body>
                            :
                            <Card.Body>No Subjects Allocated to you. Please Contact Admininistrator</Card.Body>
                    }
                </Card>

                <Card className="table-responsive p-3">
                    <Table bordered className="p-0">
                        <thead>
                            <tr>
                                <th>CO Attainment Level</th>
                                <th>Significance</th>
                                <th>For direct attainment, 50% of CIE and 50% of SEE marks are considered</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Level 3</td>
                                <td>60% and above students should have scored {'>='} 60% of total marks</td>
                                <td>For Indirect attainment, course end survey is considered</td>
                            </tr>
                            <tr>
                                <td>Level 2</td>
                                <td>55% to 59% of students should have scored {'>='} 60% of total marks</td>
                                <td>CO attainment is 90% of Direct attainment + 10% of Indirect attainment </td>
                            </tr>
                            <tr>
                                <td>Level 1</td>
                                <td>50% to 54% of students should have scored {'>='} 60% of total marks</td>
                                <td>PO attainment = CO-PO mapping strength / 3 * CO attainment</td>
                            </tr>
                        </tbody>
                    </Table>
                </Card>
            </div>
        </main>
    );
}
