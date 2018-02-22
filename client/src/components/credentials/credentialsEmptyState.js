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
              A credential defines a set of user authentication information to be used during a scan.<br />A credential
              includes a username and a password or SSH key. Entitlements Reporting uses SSH<br />to connect to servers
              on the network and uses credentials to access those servers.
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
            </EmptyState.Action>
          </EmptyState>
        </Row>
      </Grid>
    );
  }
}

CredentialsEmptyState.propTypes = {
  onAddCredential: PropTypes.func,
  onAddSource: PropTypes.func
};

function mapStateToProps(state, ownProps) {
  return state;
}

export default connect(mapStateToProps)(CredentialsEmptyState);
