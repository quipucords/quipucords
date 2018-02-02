import React from 'react';
import PropTypes from 'prop-types';
import { ListView, Button, Icon, Checkbox } from 'patternfly-react';
import { helpers } from '../../common/helpers';
import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';

class CredentialListItem extends React.Component {
  renderActions() {
    const { item, onEdit, onDelete } = this.props;

    return [
      <SimpleTooltip key="editButton" id="editTip" tooltip="Edit Credential">
        <Button
          onClick={() => {
            onEdit(item);
          }}
          bsStyle="link"
          key="editButton"
        >
          <Icon type="pf" name="edit" />
        </Button>
      </SimpleTooltip>,
      <SimpleTooltip
        key="deleteButton"
        id="deleteTip"
        tooltip="Delete Credential"
      >
        <Button
          onClick={() => {
            onDelete(item);
          }}
          bsStyle="link"
          key="removeButton"
        >
          <Icon type="pf" name="delete" />
        </Button>
      </SimpleTooltip>
    ];
  }

  render() {
    const { item, onItemSelectChange } = this.props;

    let sourceTypeIcon = helpers.sourceTypeIcon(item.cred_type);

    return (
      <ListView.Item
        key={item.id}
        checkboxInput={
          <Checkbox
            checked={item.selected}
            bsClass=""
            onClick={e => onItemSelectChange(item)}
          />
        }
        actions={this.renderActions()}
        leftContent={
          <SimpleTooltip
            id="credentialTypeTip"
            tooltip={helpers.sourceTypeString(item.cred_type)}
          >
            <ListView.Icon
              type={sourceTypeIcon.type}
              name={sourceTypeIcon.name}
            />
          </SimpleTooltip>
        }
        heading={item.name}
        description={
          <SimpleTooltip id="methodTip" tooltip="Authorization Type">
            {helpers.authorizationTypeString(item.auth_type)}
          </SimpleTooltip>
        }
        additionalInfo={[
          <ListView.InfoItem
            key="userName"
            className="list-view-info-item-text-count"
          >
            <SimpleTooltip
              id="userTip"
              tooltip={
                item.authType === 'becomeUser' ? 'Become User' : 'Username'
              }
            >
              {item.authType === 'becomeUser'
                ? item.become_user
                : item.username}
            </SimpleTooltip>
          </ListView.InfoItem>,
          <ListView.InfoItem
            key="becomeMethod"
            className="list-view-info-item-text-count"
          >
            <SimpleTooltip id="methodTip" tooltip="Become Method">
              {item.authType === 'becomeUser' ? item.become_method : ''}
            </SimpleTooltip>
          </ListView.InfoItem>
        ]}
      />
    );
  }
}

CredentialListItem.propTypes = {
  item: PropTypes.object,
  onItemSelectChange: PropTypes.func,
  onEdit: PropTypes.func,
  onDelete: PropTypes.func
};

export { CredentialListItem };
