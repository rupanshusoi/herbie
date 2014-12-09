#lang racket

(require herbie/alternative)
(require herbie/programs)
(require herbie/points)

(provide (struct-out test) *tests* casio-test test-program test-samplers
         (all-from-out herbie/points))

(define (unfold-let expr)
  (match expr
    [`(let* ,vars ,body)
     (let loop ([vars vars] [body body])
       (if (null? vars)
           body
           (let ([var (caar vars)] [val (cadar vars)])
             (loop (map (replace-var var val) (cdr vars))
                   ((replace-var var val) body)))))]
    [`(,head ,args ...)
     (cons head (map unfold-let args))]
    [x
     x]))

(define (expand-associativity expr)
  (match expr
    [(list (? (curryr member '(+ - * /)) op) a ..2 b)
     (list op
           (expand-associativity (cons op a))
           (expand-associativity b))]
    [(list op a ...)
     (cons op (map expand-associativity a))]
    [_
     expr]))

(define ((replace-var var val) expr)
  (cond
   [(eq? expr var) val]
   [(list? expr)
    (cons (car expr) (map (replace-var var val) (cdr expr)))]
   [#t
    expr]))

(define (compile-program prog)
  (expand-associativity (unfold-let prog)))

(define (test-program test)
  `(λ ,(test-vars test) ,(test-input test)))

(struct test (name vars sampling-expr input output) #:prefab)
(define *tests* (make-parameter '()))

(define (get-sampler expr)
  (match expr
    ['float sample-float]
    ['double sample-double]
    ['default sample-default]
    [`(positive ,e) (compose (curry map abs) (get-sampler e))]
    [`(uniform ,a ,b) (sample-uniform a b)]
    ['integer sample-integer]
    [`expbucket sample-expbucket]))

(define (test-samplers test)
  (for/list ([var (test-vars test)] [samp (test-sampling-expr test)])
    (cons var (get-sampler samp))))

(define (save-test t)
  (*tests* (cons t (*tests*))))

(define-syntax (casio-test stx)
  (define (var&dist expr)
    (syntax-case expr ()
      [[var samp] (cons #'var #'samp)]
      [var (cons #'var #'default)]))

  (syntax-case stx ()
    [(_ (vars ...) name input output)
     (let* ([parse-args (map var&dist (syntax->list #'(vars ...)))])
       (with-syntax ([vars (map car parse-args)]
                     [samp (map cdr parse-args)])
         #'(save-test (test name 'vars 'samp (compile-program 'input) (compile-program 'output)))))]
    [(_ (vars ...) name input)
     (let* ([parse-args (map var&dist (syntax->list #'(vars ...)))])
       (with-syntax ([vars (map car parse-args)]
                     [samp (map cdr parse-args)])
       #'(save-test (test name 'vars 'samp (compile-program 'input) #f))))]))