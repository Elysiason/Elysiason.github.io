# Jacobi Method

## Position of Jacobi Method

Jacobi Method is a fundamental algorithm and useful for dealing with large systems

## What is Jacobi Method

When we try to address the linear equations like

$$
Ax = b
$$
A is a square matrix.x is the vector that we want to know.b is a vector we already know.
In this method,we decompose A into its diagonal component D and the remainder R

$$
 A = D + R
 $$
So the equation can be rewritten as:

$$
 Dx = b - Rx
 $$
According to the equation above,we can get the iterative formula:

$$
x^{k+1} = D^{-1}(b-Rx^{k})
$$
So the iterative formula is what we want

But according to the method we explained above,we have many questions.

- Why do we decompose A into its diagonal component D and the remainder R

- Why we iterate

- Is the iteration reliable
We will try to answer them.

## Where does it come from

According to the reference I found, this method actually comes from Splitting methods.
If we have a matrix A such that A = M - N and M is nonsingular, we refer to M and N as a splitting of the matrix A.
So we have

$$x^{k+1}=M^{-1}(b+Nx^{k})$$
In this choice,we can D is easy to invert.So we come up with it.
But now I don’t know how we can come up with Splitting methods.

## The iteration

The Iteration idea comes from that if we know other element in x except x[i],we can get it from others.Through this,we can get closer to the real x.It converges because of fixed-point iteration specifics.

## Reliability

We define

$$e^{k} = x^{k} - x$$.

$$Ax = b$$.So according to the

$$x^{k+1} = D^{-1}(b-Rx^{k})$$,we get

$$
e^{k+1} + x = D^{-1}(Ax-R(e^{k}+x))
$$

$$
e^{k+1} + x = D^{-1}(Dx-Re^{k})
$$

$$
e^{k+1} = -D^{-1}Re^{k}
$$
It can converge

## limitation

We can get the assumption from our analysis.

- D can invert.So the coefficient matrix A has no zeros on its main diagonal.

- \(e^{k+1} = -D^{-1}Re^{k}\) need to converge.So The A is diagonally doominant

## Reference

- GeeksforGeeks. Jacobian Method. [https://www.geeksforgeeks.org/jacobian-method/](https://www.geeksforgeeks.org/jacobian-method/).

- Why is the Jacobi method defined the way it is? [https://math.stackexchange.com/questions/1115591/why-is-the-jacobi-method-defined-the-way-it-is](https://math.stackexchange.com/questions/1115489/solving-an-equation-by-laplace-transform/1115591#1115591).
