import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Button, EmptyState, Grid, Row } from 'patternfly-react';

class SourcesEmptyState extends React.Component {
  render() {
    return (
      <Grid fluid>
        <Row>
          <EmptyState className="full-page-blank-slate">
            <EmptyState.Icon />
            <EmptyState.Title>Welcome to Red Hat Entitlements Reporting</EmptyState.Title>
            <EmptyState.Info>
              A source defines a collection of network information, including IP addresses or host names,<br /> or
              systems management solution information, in addition to SSH ports and SSH credentials
            </EmptyState.Info>
            <EmptyState.Action>
              <Button bsStyle="primary" bsSize="large" onClick={this.props.onAddSource}>
                Add Source
              </Button>
            </EmptyState.Action>
          </EmptyState>
        </Row>
      </Grid>
    );
  }
}

SourcesEmptyState.propTypes = {
  onAddSource: PropTypes.func
};

function mapStateToProps(state, ownProps) {
  return state;
}

export default connect(mapStateToProps)(SourcesEmptyState);
