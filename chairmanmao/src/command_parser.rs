use twilight_model::id::{Id, marker::UserMarker};

pub struct Parser {
    chars: Vec<char>,
    idx: usize,
}

impl Parser {
    pub fn new(message: &str) -> Parser {
        let chars = message.chars().collect::<Vec<char>>();
        Parser {
            chars,
            idx: 0,
        }
    }

    fn consume_leading_whitespace(&mut self) -> usize {
        let mut count = 0;
        while self.idx < self.chars.len() {
            let ch = self.chars[self.idx];
            if ch == ' ' {
                self.idx += 1;
                count += 1;
            } else {
                break;
            }
        }
        count
    }

    fn peek(&self) -> Option<char> {
        self.chars.get(self.idx).copied()
    }

    fn consume(&mut self) -> Option<char> {
        let result = self.peek();
        self.idx += 1;
        result
    }

    fn consume_char(&mut self, expected_char: char) -> bool {
        if let Some(ch) = self.consume() {
            ch == expected_char
        } else {
            false
        }
    }

    fn consume_until(&mut self, end_char: char) -> Option<String> {
        let mut result = String::new();

        while let Some(ch) = self.consume() {
            if ch == end_char {
                return Some(result);
            } else {
                result.push(ch);
            }
        }
        None
    }

    pub fn parse_command(&mut self) -> Option<String> {
        self.consume_char('!');
        let mut result = String::new();

        while let Some(ch) = self.consume() {
            if ch == ' ' {
                break
            } else {
                result.push(ch);
            }
        }
        Some(result)
    }

    pub fn parse_user_id(&mut self) -> Option<Id<UserMarker>> {
        // Example: <@!928461308166926427>

        self.consume_leading_whitespace();
        self.consume_char('<');
        self.consume_char('@');
        self.consume_char('!');
        let user_id_str = self.consume_until('>')?;
        let user_id = user_id_str.parse::<u64>().ok()?;
        Some(Id::new(user_id))
    }

    pub fn parse_rest(&mut self) -> String {
        self.consume_leading_whitespace();
        let mut result = String::new();

        while let Some(ch) = self.consume() {
            result.push(ch);
        }
        result
    }

    pub fn parse_integer(&mut self) -> Option<isize> {
        self.consume_leading_whitespace();
        let mut result = String::new();

        while let Some(ch) = self.consume() {
            if ch == '-' || ch.is_numeric() {
                result.push(ch);
            } else {
                break;
            }
        }
        let value = result.parse::<isize>().ok()?;
        Some(value)
    }

    pub fn end(&self) -> Option<()> {
        match self.peek() {
            Some(_ch) => None,
            None => Some(()),
        }
    }
}

#[cfg(test)]
mod test {
    /*
    use super::*;

    #[test]
    fn parse_register() {
        let mut parser = Parser::new("!register <@!928461308166926427>");
        let command = parser.parse_command();
        let user_id = parser.parse_user_id();
        parser.end().unwrap();
        assert_eq!(command, Some("register".to_string()));
        assert_eq!(user_id, Some(UserId(928461308166926427)));
    }

    #[test]
    fn parse_honor() {
        let mut parser = Parser::new("!honor <@!928461308166926427> 10 You smell nice.");
        let command = parser.parse_command();
        let user_id = parser.parse_user_id();
        let amount = parser.parse_integer();
        let reason = parser.parse_rest();
        parser.end().unwrap();

        assert_eq!(command, Some("honor".to_string()));
        assert_eq!(user_id, Some(UserId(928461308166926427)));
        assert_eq!(amount, Some(10));
        assert_eq!(reason, "You smell nice.".to_string());
    }
    */
}

