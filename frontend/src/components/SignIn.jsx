import { sendPasswordResetEmail, signInWithEmailAndPassword, signInWithPopup, GoogleAuthProvider, signOut } from "firebase/auth";
import { auth } from "../firebase";
import React, { useContext, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ToastContainer, toast } from "react-toastify";
import { Button, Card, Col, Row, Form, Container } from 'react-bootstrap';
import { AuthContext } from "./AuthContext";
import serverRequest from "../helper/serverRequest";
import "react-toastify/dist/ReactToastify.css";

export default function SignIn() {
    const { user, setUser } = useContext(AuthContext);
    const refEmail = useRef(null);
    const refPassword = useRef(null);
    const navigate = useNavigate();

    useEffect(() => {
        document.title = "Login";
        if (user)
            navigate(user.userType === "Admin" ? "/admin" : "/home");
    }, [navigate, user]);

    const toasts = (message, type) => {
        type(message, {
            position: "top-center",
            autoClose: 2000,
            hideProgressBar: false,
            closeOnClick: true,
            pauseOnHover: true,
            draggable: true,
            progress: undefined,
            theme: "colored",
        });
    };

    const validateEmail = (email) => {
        const regex = /^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/;
        return regex.test(email);
    };

    const validatePassword = (password) => {
        const regex = /^(?=.*[0-9])(?=.*[!@#$%^&*])[a-zA-Z0-9!@#$%^&*]{6,16}$/;
        return regex.test(password);
    };

    const handleForgotPassword = async (e) => {
        e.preventDefault();

        const email = refEmail.current.value;

        if (!validateEmail(email)) {
            toasts("Invalid Email-Id!", toast.error);
            return;
        }

        try {
            await sendPasswordResetEmail(auth, email);
            toasts("Password reset email sent successfully!", toast.success);
        } catch (error) {
            console.error(error);
            toasts(error.message, toast.error);
        }
    };

    const handleGoogleSignIn = async () => {
        const provider = new GoogleAuthProvider();
        try {
            const userCredential = await signInWithPopup(auth, provider);
            const { uid } = userCredential.user;
            const tokenResult = await auth.currentUser.getIdTokenResult();
            const token = tokenResult.token;
            const { userType } = tokenResult.claims;

            if (!userType)
                throw new Error("UserType not set");

            setUser({ uid: uid, userType: userType, userMail: userCredential.user.email, token: token });

            const endpoint = "http://localhost:8000/login";
            const body = { email: userCredential.user.email, userId: uid, userType };
            await serverRequest(endpoint, "POST", body);

            navigate(userType === "Admin" ? "/admin" : "/home");
            toasts(`Successfully! Logged in as ${userCredential.user.email}`, toast.success);
        } catch (error) {
            console.error(error);
            setUser(null);
            await signOut(auth);
            toasts(error.message, toast.error);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const email = refEmail.current.value;
        const password = refPassword.current.value;

        if (!validateEmail(email)) {
            toasts("Invalid Email-Id!", toast.error);
            return;
        }

        if (!validatePassword(password)) {
            toasts("Invalid Password!", toast.error);
            return;
        }

        try {
            const userCredential = await signInWithEmailAndPassword(auth, email, password);
            const { uid } = userCredential.user;
            const tokenResult = await auth.currentUser.getIdTokenResult();
            const token = tokenResult.token;
            const { userType } = tokenResult.claims;

            if (!userType)
                throw new Error("UserType not set");
            setUser({ uid: uid, userType: userType, userMail: email, token: token });

            const endpoint = "http://localhost:8000/login";
            const body = { email, userId: uid, userType };
            await serverRequest(endpoint, "POST", body);

            navigate(userType === "Admin" ? "/admin" : "/home");
            toasts(`Successfully! Logged in as ${email}`, toast.success);
        } catch (error) {
            console.error(error);
            setUser(null);
            await signOut(auth);
            toasts(error.message, toast.error);
        }
    };

    return (
        <Container className="pt-5">
            <Row className="justify-content-center align-items-center">
                <Col xs={12} sm={10} md={7} lg={6} xl={5}>
                    <Card bg="dark" text="white" className="rounded">
                        <Card.Body className="py-5 px-3 text-center">
                            <Form onSubmit={handleSubmit}>
                                <h2 className="fw-bold mb-2 text-uppercase">Login</h2>
                                <p className="text-white-50 mb-5">
                                    Please enter your email and password!
                                </p>

                                <Form.Group as={Row} className="align-items-center m-4">
                                    <Form.Label column sm={4} htmlFor="typeEmailX" className="text-right" >
                                        Email &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
                                    </Form.Label>
                                    <Col sm={8}>
                                        <Form.Control type="email" id="typeEmailX" placeholder="Enter Email" ref={refEmail} />
                                    </Col>
                                </Form.Group>

                                <Form.Group as={Row} className="align-items-center m-4">
                                    <Form.Label column sm={4} htmlFor="typePasswordX" className="text-right" >
                                        Password
                                    </Form.Label>
                                    <Col sm={8}>
                                        <Form.Control type="password" id="typePasswordX" placeholder="Enter Password" ref={refPassword} />
                                    </Col>
                                </Form.Group>

                                <p className="small mb-5 pb-lg-2 text-white-50" onClick={handleForgotPassword} >
                                    Forgot password?
                                </p>

                                <Button variant="outline-light" size="lg" className="px-5" type="submit" >
                                    Login
                                </Button>

                                <div className="text-center mt-4 pt-1">
                                    {/* <a href="#" className="text-white">
                                        <i className="fab fa-facebook-f fa-lg"></i>
                                    </a>
                                    <a href="#" className="text-white">
                                        <i className="fab fa-twitter fa-lg mx-4 px-2"></i>
                                    </a> */}
                                    <a href="#" className="text-white" onClick={handleGoogleSignIn}>
                                        <i className="fab fa-google fa-lg"></i>
                                    </a>
                                </div>
                            </Form>
                        </Card.Body>
                    </Card>
                    <ToastContainer />
                </Col>
            </Row>
        </Container>
    );
}