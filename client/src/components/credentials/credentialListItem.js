import React from 'react';
import PropTypes from 'prop-types';
import { ListView, Button, Grid, Icon, Checkbox } from 'patternfly-react';
import { helpers } from '../../common/helpers';
import { SimpleTooltip } from '../simpleTooltIp/simpleTooltip';

class CredentialListItem extends React.Component {
  constructor() {
    super();

    helpers.bindMethods(this, ['toggleExpand', 'closeExpand']);
  }

  toggleExpand(expandType) {
    const { item } = this.props;

    if (expandType === item.expandType) {
      item.expanded = !item.expanded;
    } else {
      item.expanded = true;
      item.expandType = expandType;
    }
    this.forceUpdate();
  }

  closeExpand() {
    const { item } = this.props;
    item.expanded = false;
    this.forceUpdate();
  }

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

  renderStatusItems() {
    const { item } = this.props;

    let sourceCount = item.sources ? item.sources.length : 0;

    return [
      <ListView.InfoItem
        key="sources"
        className={
          'list-view-info-item-icon-count ' +
          (sourceCount === 0 ? 'invisible' : '')
        }
      >
        <ListView.Expand
          expanded={item.expanded && item.expandType === 'sources'}
          toggleExpanded={() => {
            this.toggleExpand('sources');
          }}
        >
          <strong>{sourceCount}</strong>
          {sourceCount === 1 ? ' Source' : ' Sources'}
        </ListView.Expand>
      </ListView.InfoItem>
    ];
  }

  renderExpansionContents() {
    const { item } = this.props;

    switch (item.expandType) {
      case 'sources':
        return (
          <Grid fluid>
            {item.sources &&
              item.sources.map((item, index) => (
                <Grid.Row key={index}>
                  <Grid.Col xs={12} sm={4}>
                    <span>
                      <Icon type="pf" name="server-group" />
                      &nbsp; {item}
                    </span>
                  </Grid.Col>
                </Grid.Row>
              ))}
          </Grid>
        );
      default:
        return null;
    }
  }

  render() {
    const { item, onItemSelectChange } = this.props;

    let sourceTypeIcon = helpers.sourceTypeIcon(item.cred_type);

    return (
      <ListView.Item
        key={item.id}
        className="quipucords-credential-list-item"
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
        additionalInfo={this.renderStatusItems()}
        compoundExpand
        compoundExpanded={item.expanded}
        onCloseCompoundExpand={this.closeExpand}
      >
        {this.renderExpansionContents()}
      </ListView.Item>
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
