import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux';

import { Button, DropdownButton, EmptyState, Grid, MenuItem, Row } from 'patternfly-react';

class CredentialsEmptyState extends React.Component {
  render() {
    return (
      <Grid fluid>
        <Row>
          <EmptyState className="full-page-blank-slate">
            <EmptyState.Icon />
            <EmptyState.Title>Welcome to Red Hat Entitlements Reporting</EmptyState.Title>
            <EmptyState.Info>
              There are no stored credentials for Red Hat Entitlements Reporting<br />
              You can add credentials here or you can add some networks to search for Red Hat products. You can add a
              source here or download them from a spreadsheet template.
            </EmptyState.Info>
            <EmptyState.Action>
              <DropdownButton bsStyle="primary" title="Add Credential" pullRight id="createCredentialButton">
                <MenuItem eventKey="1" onClick={() => this.props.onAddCredential('network')}>
                  Network Credential
                </MenuItem>
                <MenuItem eventKey="2" onClick={() => this.props.onAddCredential('satellite')}>
                  Satellite Credential
                </MenuItem>
                <MenuItem eventKey="2" onClick={() => this.props.onAddCredential('vcenter')}>
                  VCenter Credential
                </MenuItem>
              </DropdownButton>
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
