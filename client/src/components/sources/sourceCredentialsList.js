import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Icon } from 'patternfly-react';

class SourceCredentialsList extends React.Component {
  constructor() {
    super();

    this.state = {
      credentials: []
    };
  }

  componentDidMount() {
    const { source } = this.props;
    let credentials = [...source.credentials];

    credentials.sort((item1, item2) => {
      return item1.name.localeCompare(item2.name);
    });
    this.setState({ credentials: credentials });
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.source !== this.props.source) {
      const { source } = this.nextProps;
      let credentials = [...source.credentials];

      credentials.sort((item1, item2) => {
        return item1.name.localeCompare(item2.name);
      });
      this.setState({ credentials: credentials });
    }
  }

  render() {
    const { credentials } = this.state;

    return (
      <Grid fluid>
        {credentials.map((item, index) => (
          <Grid.Row key={index}>
            <Grid.Col xs={12} sm={4}>
              <span>
                <Icon type="fa" name="key" />
                &nbsp; {item.name}
              </span>
            </Grid.Col>
          </Grid.Row>
        ))}
      </Grid>
    );
  }
}

SourceCredentialsList.propTypes = {
  source: PropTypes.object
};

export { SourceCredentialsList };
