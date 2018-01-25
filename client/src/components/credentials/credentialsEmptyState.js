import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Button, EmptyState, Grid, Row } from 'patternfly-react';

class CredentialsEmptyState extends React.Component {
  render() {
    return (
      <Grid fluid>
        <Row>
          <EmptyState className="full-page-blank-slate">
            <EmptyState.Icon />
            <EmptyState.Title>
              Welcome to Red Hat Entitlements Reporting
            </EmptyState.Title>
            <EmptyState.Info>
              There are no stored credentials for Red Hat Entitlements Reporting<br />
              You can add credentials here or you can add some networks to
              search for Red Hat products. You can add a source here or download
              them from a spreadsheet template.
            </EmptyState.Info>
            <EmptyState.Action>
              <Button
                bsStyle="primary"
                bsSize="large"
                onClick={this.props.onAddCredential}
              >
                Add Credential
              </Button>
            </EmptyState.Action>
            <EmptyState.Action secondary>
              <Button bsStyle="default" onClick={this.props.onAddSource}>
                Add Source
              </Button>
              <Button bsStyle="default" onClick={this.props.onImportSources}>
                Import Credentials
              </Button>
            </EmptyState.Action>
          </EmptyState>
        </Row>
      </Grid>
    );
  }
}

CredentialsEmptyState.propTypes = {
  onAddCredential: PropTypes.func,
  onAddSource: PropTypes.func,
  onImportSources: PropTypes.func
};

function mapStateToProps(state, ownProps) {
  return state;
}

export default connect(mapStateToProps)(CredentialsEmptyState);
