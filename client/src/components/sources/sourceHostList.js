import React from 'react';
import PropTypes from 'prop-types';
import { Grid, Icon } from 'patternfly-react';

class SourceHostsList extends React.Component {
  componentWillReceiveProps(nextProps) {
    if (nextProps.hosts !== this.props.hosts) {
      nextProps.hosts &&
        nextProps.hosts.sort((item1, item2) => {
          return item1.localeCompare(item2);
        });
    }
  }

  render() {
    const { hosts, status } = this.props;

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

SourceHostsList.propTypes = {
  hosts: PropTypes.array,
  status: PropTypes.string
};

export { SourceHostsList };
