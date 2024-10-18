from emolang.lexer import TokenType, SyntaxException
from emolang.parser.nodes import (
    AssignmentNode,
    AdditionNode,
    MultiplicationNode,
    IfNode,
    ElseIfNode,
    ElseNode,
    SubtractionNode,
    ModulusNode,
    DivisionNode,
    ExponentNode,
    BlockNode,
    NumberLiteralNode,
    PrintNode,
    StringLiteralNode,
    VariableNode,
    BinaryOperationContext,
    AndNode,
    EqualsNode,
    GreaterNode,
    GreaterEqualsNode,
    LessNode,
    LessEqualsNode,
    NotNode,
    NotEqualsNode,
    OrNode,
    BooleanLiteralNode,
    UnaryOperationContext
)


class Parser:
    """
    The Parser class is responsible for transforming a list of tokens into an Abstract Syntax Tree (AST).
    It handles parsing variable assignments, expressions, operations, and print statements.
    The algorithm used here to construct the AST is recursive descent parsing.
    """

    def __init__(self, tokens):
        """
        Initializes the parser with a list of tokens.

        :param tokens: The list of tokens generated by the lexer.
        """
        self._tokens = tokens
        self._current = 0

    def parse(self):
        """
        The main entry point for parsing. It loops through the tokens and parses each one,
        generating a BlockNode (AST root) containing all parsed nodes.

        :return: BlockNode representing the entire parsed program.
        """
        nodes = []
        while self._in_bounds(self._current) and not self._is_eof_token():
            node = self._handle_token()
            nodes.append(node)
        return BlockNode(nodes)

    def _in_bounds(self, index):
        """
        Checks if the given index is within the bounds of the token list.

        :param index: Index to check.
        :return: True if the index is within the bounds, False otherwise.
        """
        return index < len(self._tokens)

    def _is_eof_token(self):
        """
        Checks if the current token is the end-of-file (EOF) token.

        :return: True if the current token is EOF, False otherwise.
        """
        token = self._current_token()
        return token.is_token_type(TokenType.EOF)

    def _current_token(self):
        """
        Retrieves the current token being processed.

        :return: The current token.
        """
        return self._retrieve_token(self._current)

    def _handle_token(self, index=None, context=None):
        """
        Handles a token based on its type. This function delegates token-specific logic to
        different parsing methods (e.g., print, identifier, variable).

        :param index: The current token index (defaults to _current).
        :param context: Context for operation nodes.
        :return: A parsed node corresponding to the token.
        """
        if index is None:
            index = self._current
        token = self._retrieve_token(index)
        if token.is_token_type(TokenType.PRINT):
            return self._parse_print_token()
        if token.is_token_type(TokenType.IDENTIFIER):
            return self._parse_identifier_token(index)
        if token.is_token_type(TokenType.VAR):
            return self._parse_var_token()
        if token.is_token_type(TokenType.IF):
            return self._parse_if_statement()
        if token.get_token_type() in TokenType.literal_types():
            return self._parse_literal(token)
        if token.get_token_type() in TokenType.operation_types():
            return self._parse_operation(token, context)

    def _retrieve_token(self, index):
        """
        Retrieves the token at a specified index.

        :param index: The index of the token.
        :return: The token at the specified index.
        """
        return self._tokens[index]

    def _parse_print_token(self):
        """
        Parses a print statement. The expected structure is:
        🗣️ <expression> ;

        :return: PrintNode representing the print statement.
        """
        self._validate_token({TokenType.PRINT}, "Expected '🗣️' for print statement.")
        node_to_print = self._parse_expression()
        self._validate_token({TokenType.SEMI_COLON}, "Expected ';' to terminate statement.")
        return PrintNode(node_to_print)

    def _validate_token(self, valid_token_types, error_message):
        """
        Validates that the current token matches one of the expected types. Raises a SyntaxException if not.

        :param valid_token_types: A set of token types that are valid while parsing this token.
        :param error_message: The error message to raise if validation fails.
        """
        next_token = self._retrieve_token(self._current)
        if next_token.get_token_type() not in valid_token_types:
            raise SyntaxException(next_token.get_line(), error_message)
        self._current += 1

    def _parse_identifier_token(self, index):
        """
        Parses an identifier token, which represents a variable.

        :param index: The index of the identifier token.
        :return: VariableNode representing the variable.
        """
        identifier_token = self._retrieve_token(index)
        return VariableNode(identifier_token.get_lexeme())

    def _parse_var_token(self):
        """
        Parses a variable declaration or assignment. The expected structure is:
        🥸 <identifier> ✍️ <expression> ;

        :return: AssignmentNode representing the variable assignment.
        """
        self._validate_token({TokenType.VAR}, "Expected '🥸' to indicate variable.")
        variable_node = self._parse_identifier_token(self._current)
        self._validate_token({TokenType.IDENTIFIER}, "Expected an identifier for assignment.")
        self._validate_token({TokenType.EQUAL}, "Expected '✍️' for assignment.")
        value_node = self._parse_expression()
        self._validate_token({TokenType.SEMI_COLON}, "Expected ';' to terminate the statement.")
        return AssignmentNode(variable_node, value_node)

    def _parse_expression(self):
        """
        Parses an expression up to the specified end token (such as a semicolon or a right brace).

        :return: The root node of the parsed expression.
        """
        end_of_expression_index = self._find_end_of_expression_index()
        node = self._parse_expression_recursive(self._current, end_of_expression_index - 1)
        self._current = end_of_expression_index
        return node

    def _find_end_of_expression_index(self):
        """
        Finds the index of the end of the expression specified token (such as a semicolon).
        This is done by iterating until it encounters a token that shouldn't be found in
        an expression.

        :return: The index of the end of expression.
        """
        index = self._current
        valid_expression_tokens = TokenType.valid_expression_types()
        while self._retrieve_token(index).get_token_type() in valid_expression_tokens:
            index += 1
        return index

    def _parse_expression_recursive(self, left_index, right_index):
        """
        Recursively parses an expression within the given token range. Handles precedence and parentheses.

        :param left_index: The left bound of the token range.
        :param right_index: The right bound of the token range.
        :return: The parsed expression node.
        """
        left_token, right_token = self._retrieve_token(left_index), self._retrieve_token(right_index)
        index_delta = right_index - left_index
        if index_delta == 0:
            token_type = left_token.get_token_type()
            if token_type not in TokenType.valid_expression_types():
                raise SyntaxException(left_token.get_line(), f"Invalid token in expression: {token_type}")
            return self._handle_token(left_index)
        if self._is_nested_parens(left_index, right_index):
            return self._parse_expression_recursive(left_index + 1, right_index - 1)
        operator_precedence = [
            {TokenType.OR},
            {TokenType.AND},
            {TokenType.EQUAL_EQUAL, TokenType.GREATER, TokenType.GREATER_EQUAL, TokenType.LESS_EQUAL, TokenType.LESS, TokenType.BANG_EQUAL},
            {TokenType.BANG},
            {TokenType.MINUS, TokenType.PLUS},
            {TokenType.MULTIPLY, TokenType.DIVIDE, TokenType.MODULUS},
            {TokenType.EXPONENT}
        ]
        for operators in operator_precedence:
            index = left_index
            while index < right_index:
                token = self._retrieve_token(index)
                if token.is_token_type(TokenType.LEFT_PAREN):
                    index = self._skip_parentheses(index, right_index)
                node = self._handle_by_operations(operators, left_index, right_index, index)
                if node:
                    return node
                index += 1

        raise SyntaxException(
            self._retrieve_token(left_index).get_line(),
            "Invalid expression: no valid operations found."
        )

    def _is_nested_parens(self, left_index, right_index):
        """
        Checks if the parentheses between the given left and right indices are nested,
        meaning that the parentheses are part of the same nested group.

        :param left_index: The index of the left parenthesis.
        :param right_index: The index of the right bound for the search.
        :return: `True` if the parentheses are nested, `False` otherwise.
        """
        if not self._within_parens(left_index, right_index):
            return False

        paren_counter, end_index = self._find_parenthesis_count(left_index, right_index)
        return paren_counter == 0 and end_index == right_index

    def _find_parenthesis_count(self, left_index, right_index):
        """
        Scans the tokens between `left_index` and `right_index` to find where a set of parentheses closes
        and the balance of parentheses between the bounds.

        :param left_index: The index of the left parenthesis `'('` where the search begins.
        :param right_index: The index of the right bound for the search.
        :return: A tuple containing:
            - `paren_counter` (int): The final count of parentheses (should be zero if parentheses are balanced).
            - `current_index` (int): The index at which the parentheses balance returns to zero.
        :raises SyntaxException: If there are unmatched left or right parentheses within the given range.
        """
        paren_counter = 0
        current_index = left_index
        while current_index <= right_index:
            token = self._retrieve_token(current_index)
            if token.is_token_type(TokenType.LEFT_PAREN):
                paren_counter += 1
            if token.is_token_type(TokenType.RIGHT_PAREN):
                paren_counter -= 1
            if paren_counter == 0:
                break
            current_index += 1

        token_line = self._retrieve_token(right_index).get_line()
        if paren_counter > 0:
            raise SyntaxException(token_line, 'Left parenthesis missing closing right.')
        elif paren_counter < 0:
            raise SyntaxException(token_line, 'Right parenthesis missing corresponding left.')
        return paren_counter, current_index

    def _within_parens(self, left_index, right_index):
        """
        Checks if the given tokens are within parentheses.

        :param left_index: The left token index.
        :param right_index: The right token index.
        :return: True if the tokens are within parentheses, False otherwise.
        """
        left_token, right_token = self._retrieve_token(left_index), self._retrieve_token(right_index)
        return left_token.is_token_type(TokenType.LEFT_PAREN) and right_token.is_token_type(TokenType.RIGHT_PAREN)

    def _skip_parentheses(self, left_index, right_index):
        """
        Skips over a section of tokens enclosed in parentheses.

        :param left_index: The starting index (left parenthesis).
        :param right_index: The ending index.
        :return: The index of the token after the closing parenthesis.
        """
        paren_counter, end_index = self._find_parenthesis_count(left_index, right_index)
        return min(end_index + 1, right_index)

    def _handle_by_operations(self, operations, left_index, right_index, index):
        """
        Handles binary and unary operations based on operator precedence.

        :param operations: Set of operations to process.
        :param left_index: Left bound of the expression.
        :param right_index: Right bound of the expression.
        :param index: Current token index.
        :return: Node representing the operation, or None if no operation was found.
        """
        token = self._retrieve_token(index)
        token_type = token.get_token_type()
        if token_type in operations:
            if token_type in TokenType.unary_operations():
                return self._handle_unary_operation(index, right_index)
            else:
                return self._handle_binary_operation(left_index, index, right_index)

    def _handle_unary_operation(self, index, right_index):
        """
        Handles unary operations (such as negation).

        :param index: The index of the unary operator.
        :param right_index: The right bound of the expression.
        :return: Node representing the unary operation.
        """
        token = self._retrieve_token(index)
        right_node = self._parse_expression_recursive(index + 1, right_index)
        if right_node is None:
            raise SyntaxException(token.get_line(), "Invalid expression: missing right operand.")
        context = UnaryOperationContext(right_node)
        return self._handle_token(index, context)

    def _handle_binary_operation(self, left_index, index, right_index):
        """
        Handles binary operations (such as addition, subtraction, etc.).

        :param left_index: Left bound of the left operand.
        :param index: The index of the operator.
        :param right_index: Right bound of the right operand.
        :return: Node representing the binary operation.
        """
        token = self._retrieve_token(index)
        left_node = self._parse_expression_recursive(left_index, index - 1)
        if left_node is None:
            raise SyntaxException(token.get_line(), "Invalid expression: missing left operand.")

        right_node = self._parse_expression_recursive(index + 1, right_index)
        if right_node is None:
            raise SyntaxException(token.get_line(), "Invalid expression: missing right operand.")

        context = BinaryOperationContext(left_node, right_node)
        return self._handle_token(index, context)

    def _parse_if_statement(self):
        """
        Parses an if statement in the source code.

        :return: An IfNode representing the parsed if statement.
        """
        self._validate_token({TokenType.IF}, "Expected '🤔' for if statement.")
        condition_node, block_node = self._parse_conditional()
        next_conditional = self._parse_next_if_conditional()
        return IfNode(condition_node, block_node, next_conditional)

    def _parse_conditional(self):
        """
        Parse the condition and block of an if statement.

        :return: Tuple containing the condition node and block node.
        """
        condition_node = self._parse_expression()
        self._validate_token({TokenType.LEFT_BRACE}, "Expected '{' to begin if statement block.")
        if_block_node = self._parse_block()
        self._validate_token({TokenType.RIGHT_BRACE}, "Expected '}' to begin if statement block.")
        return condition_node, if_block_node

    def _parse_block(self):
        """
        Parses a block of code enclosed in curly braces `{}`. If no closing brace
        is found, it raises a SyntaxException.

        :return: A BlockNode representing the parsed block of code.
        """
        nodes = []
        while not self._current_token().is_token_type(TokenType.RIGHT_BRACE):
            if self._is_eof_token():
                raise SyntaxException(self._current_token().get_line(), "Missing closing right brace.")
            node = self._handle_token()
            nodes.append(node)
        return BlockNode(nodes)

    def _parse_next_if_conditional(self):
        """
        Parses an optional elseif block chain in an if statement.

        :return: A BlockNode representing the elseif node or None if not present.
        """
        if self._current_token().is_token_type(TokenType.ELSE):
            return self._parse_else()
        if self._current_token().get_token_type() not in TokenType.if_statement_tokens():
            return
        if self._current_token().is_token_type(TokenType.ELSEIF):
            self._validate_token({TokenType.ELSEIF}, "Expected '🙈' for elseif statement.")
            condition_node, block_node = self._parse_conditional()
            next_conditional = self._parse_next_if_conditional()
            return ElseIfNode(condition_node, block_node, next_conditional)

    def _parse_else(self):
        """
        Parses an optional else block in an if statement.

        :return: A BlockNode representing the else block or None if no else block is present.
        """
        else_block_node = None
        if self._current_token().is_token_type(TokenType.ELSE):
            self._validate_token({TokenType.ELSE}, "Expected '💅' for else.")
            self._validate_token({TokenType.LEFT_BRACE}, "Expected '{' to begin else block.")
            else_block_node = self._parse_block()
            self._validate_token({TokenType.RIGHT_BRACE}, "Expected '}' to begin else block.")
        return ElseNode(else_block_node)

    def _parse_literal(self, token):
        """
        Parses a literal token (e.g., string, number, boolean).

        :param token: The literal token to parse.
        :return: Node representing the literal value.
        """
        if token.is_token_type(TokenType.STRING):
            return StringLiteralNode(token.get_literal())
        if token.is_token_type(TokenType.NUMBER):
            return NumberLiteralNode(token.get_literal())
        if token.is_token_type(TokenType.TRUE):
            return BooleanLiteralNode(True)
        if token.is_token_type(TokenType.FALSE):
            return BooleanLiteralNode(False)

    def _parse_operation(self, token, context):
        """
        Parses an operation token and returns the appropriate operation node based on the context.

        :param token: The operation token to parse.
        :param context: The context (unary or binary) in which the operation occurs.
        :return: The corresponding operation node.
        """
        binary_operation_map = {
            TokenType.AND: AndNode,
            TokenType.BANG_EQUAL: NotEqualsNode,
            TokenType.DIVIDE: DivisionNode,
            TokenType.EQUAL_EQUAL: EqualsNode,
            TokenType.EXPONENT: ExponentNode,
            TokenType.GREATER: GreaterNode,
            TokenType.GREATER_EQUAL: GreaterEqualsNode,
            TokenType.LESS: LessNode,
            TokenType.LESS_EQUAL: LessEqualsNode,
            TokenType.MINUS: SubtractionNode,
            TokenType.MODULUS: ModulusNode,
            TokenType.MULTIPLY: MultiplicationNode,
            TokenType.OR: OrNode,
            TokenType.PLUS: AdditionNode,
        }
        token_type = token.get_token_type()
        if token_type in binary_operation_map:
            operation_class = binary_operation_map[token_type]
            left_operand, right_operand = context.get_left_operand(), context.get_right_operand()
            return operation_class(left_operand, right_operand)

        if token.is_token_type(TokenType.BANG):
            return NotNode(context.get_operand())
