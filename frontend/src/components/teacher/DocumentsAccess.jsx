import React from "react";
import { Component } from "react";
import { Accordion, Button, Card } from 'react-bootstrap';
import serverRequest from "../../helper/serverRequest";

export default class DocumentsAccess extends Component {
    constructor(props) {
        super(props);
        this.serverLink = 'http://localhost:8000/';
        document.title = "Documents Access"
        this.state = { listOfDocs: [] };
    }

    async componentDidMount() {
        let listOfDocs = (await (await serverRequest("http://localhost:8000/getDirectoryTree")).json())['public'];
        this.setState({ listOfDocs: listOfDocs });
    }

    displayFiles(files) {
        return <Accordion className="d-grid border rounded" defaultActiveKey="0">
            {(files) ?
                files.map((file, fileIndex) => {
                    if (typeof file === "object") {
                        let key = Object.keys(file)[0];
                        return <Accordion.Item key={fileIndex}>
                            <Accordion.Header>{`${fileIndex}. ${key.split('/').at(-1)}...`}</Accordion.Header>
                            <Accordion.Body className="p-2">{this.displayFiles(file[key])}</Accordion.Body>
                        </Accordion.Item>

                    }
                    else
                        return <Button key={fileIndex} variant="outline-info" href={this.serverLink + file.replace("public/", "")} style={{ "textAlign": "left" }} className="border-light text-dark">{`${fileIndex}. ${file.split('/').at(-1)}`}</Button>
                }) : ""}
        </Accordion>
    }

    render() {
        return (
            <main className="pt-5">
                <div className="container">
                    <Card className="p-0">
                        <Card.Header className="fs-3">Documents Access</Card.Header>
                        <Card.Body>
                            {this.displayFiles(this.state.listOfDocs)}
                        </Card.Body>
                    </Card>
                </div>
            </main>
        )
    }
}