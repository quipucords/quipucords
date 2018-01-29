import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Icon } from 'patternfly-react';

class ScanHostsList extends React.Component {
  constructor() {
    super();

    this.state = {
      hosts: []
    };
  }

  componentDidMount() {
    const { hosts } = this.props;
    let sortedHosts = [...hosts];

    sortedHosts.sort((item1, item2) => {
      return item1.localeCompare(item2);
    });

    this.setState({ hosts: sortedHosts });
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.hosts !== this.props.hosts) {
      const { hosts } = nextProps;
      let sortedHosts = [...hosts];

      sortedHosts.sort((item1, item2) => {
        return item1.localeCompare(item2);
      });

      this.setState({ hosts: sortedHosts });
    }
  }

  render() {
    const { status } = this.props;
    const { hosts } = this.state;

    return (
      <Grid fluid>
        {hosts &&
          hosts.map((item, index) => (
            <Grid.Row key={index}>
              <Grid.Col xs={12} sm={4}>
                <span>
                  <Icon type="pf" name={status} />
                  &nbsp; {item}
                </span>
              </Grid.Col>
            </Grid.Row>
          ))}
      </Grid>
    );
  }
}

ScanHostsList.propTypes = {
  hosts: PropTypes.array,
  status: PropTypes.string
};

export { ScanHostsList };
